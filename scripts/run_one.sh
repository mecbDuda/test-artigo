#!/usr/bin/env bash
# Executa UMA execução (API × ferramenta × repetição) isolada num slot paralelo:
# sobe a API e o proxy do slot, restaura o estado inicial, roda a ferramenta com o
# orçamento de tempo e grava meta.json (só no fim: execução sem meta.json = incompleta).
#
# Uso (na raiz do repositório; normalmente chamado por scripts/run_parallel.py):
#   API=vampi TOOL=restler REP=1 SLOT=0 BUDGET_SEC=1800 SEED=1001 ./scripts/run_one.sh
#
# Isolamento do slot k: proxy na porta 8080+k, servidor da especificação na 8099+k,
# projeto compose fuzzexp_k e contêineres com sufixo _s<k>. Limites de CPU/memória
# vêm do ambiente (TOOL_*, API_*, PROXY_*; ver scripts/limites.sh).
# Vizinhos (execuções que rodaram ao mesmo tempo, em outros slots) são lidos de
# $ESTADO_DIR/<run_id>.vizinhos, mantido pelo run_parallel.py.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
source tools/lib.sh
: "${API:?}" "${TOOL:?}" "${REP:?}" "${BUDGET_SEC:?}" "${SEED:?}"
SLOT="${SLOT:-0}"
ESTADO_DIR="${ESTADO_DIR:-$ROOT/data/raw/.estado}"
REGISTRO_DESVIOS="${REGISTRO_DESVIOS:-$ROOT/docs/desvios.md}"
export PROXY_PORT=$((8080 + SLOT)) SCHEMA_PORT=$((8099 + SLOT)) CONTAINER_SUFFIX="_s${SLOT}"
export TOOL_CPUS="${TOOL_CPUS:-}" TOOL_MEM="${TOOL_MEM:-}" API_CPUS="${API_CPUS:-0}" API_MEM="${API_MEM:-0}" \
       PROXY_CPUS="${PROXY_CPUS:-0}" PROXY_MEM="${PROXY_MEM:-0}" API_JAVA_OPTS="${API_JAVA_OPTS:-}"
export BUDGET_SEC SEED

set -a; source "apis/$API/api.env"; set +a
run_id="${API}__${TOOL}__rep${REP}"
export OUT_DIR="$ROOT/data/raw/$run_id"
export LOG_DIR="$OUT_DIR"
export SCHEMA_PATH="$ROOT/$SCHEMA_FILE"
export SCHEMA_URL="http://localhost:$SCHEMA_PORT/$(basename "$SCHEMA_FILE")"
export BASE_URL

if [ -f "$OUT_DIR/meta.json" ]; then echo ">> $run_id já concluída, pulando"; exit 0; fi
if [ -d "$OUT_DIR" ]; then
  # execução interrompida: movida (não apagada) para data/raw/_incompletas/ e refeita
  dest="$ROOT/data/raw/_incompletas/${run_id}__$(date +%Y%m%dT%H%M%S)"
  mkdir -p "$ROOT/data/raw/_incompletas"; mv "$OUT_DIR" "$dest"
  echo "| $(date -Is) | execução refeita | \`$run_id\` estava incompleta (sem meta.json); movida para \`data/raw/_incompletas/$(basename "$dest")\` |" >> "$REGISTRO_DESVIOS"
  echo ">> $run_id estava incompleta; movida para data/raw/_incompletas/ e será refeita"
fi
mkdir -p "$OUT_DIR"
echo "=== $run_id slot=$SLOT ($(date -Is)) ==="

compose=(docker compose -p "fuzzexp_${SLOT}" -f "apis/$API/docker-compose.yml")
cleanup() {
  kill "${spec_srv:-}" 2>/dev/null || true
  # contêineres de ferramenta deste slot que tenham sobrado (interrupção no meio)
  docker ps -aq --filter "name=${CONTAINER_SUFFIX}\$" | xargs -r docker rm -f >/dev/null 2>&1 || true
  "${compose[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT
trap 'exit 143' TERM INT

# 1) estado limpo: derruba tudo (inclusive volumes) e sobe de novo
"${compose[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
"${compose[@]}" up -d || { echo "!! docker compose up falhou"; exit 1; }
healthy=0
for _ in $(seq 1 90); do curl -fsS -o /dev/null "$HEALTH_URL" 2>/dev/null && { healthy=1; break; }; sleep 2; done
[ "$healthy" = 1 ] || { echo "!! API não respondeu em $HEALTH_URL"; exit 1; }
# o reset pode falhar de forma intermitente (no VAmPI, /createdb sorteia títulos de
# livro únicos e às vezes colide); tenta de novo antes de desistir (D04)
init_ok=0
for try in 1 2 3 4 5; do
  if eval "$INIT_CMD" >/dev/null 2>&1; then init_ok=1; break; fi
  echo "   INIT_CMD falhou (tentativa $try), repetindo"; sleep 2
done
[ "$init_ok" = 1 ] || { echo "!! INIT_CMD falhou 5 vezes"; exit 1; }
echo "init_tentativas=$try" > "$OUT_DIR/init.txt"
AUTH_HEADER=""
if [ -n "${AUTH_SCRIPT:-}" ]; then
  AUTH_HEADER="$(bash "$AUTH_SCRIPT")" || AUTH_HEADER=""
  [ -n "$AUTH_HEADER" ] || { echo "!! $AUTH_SCRIPT não devolveu cabeçalho de autenticação"; exit 1; }
fi
export AUTH_HEADER
# descarta as requisições feitas pelo próprio script de preparação
: > "$OUT_DIR/flows.jsonl"

# 2) servidor estático com a especificação (mesmo arquivo para todas as ferramentas)
python3 -m http.server "$SCHEMA_PORT" --bind 127.0.0.1 -d "$(dirname "$SCHEMA_PATH")" >/dev/null 2>&1 &
spec_srv=$!
for _ in $(seq 1 20); do curl -fsS -o /dev/null "$SCHEMA_URL" 2>/dev/null && break; sleep 0.5; done
curl -fsS -o /dev/null "$SCHEMA_URL" || { echo "!! servidor da especificação não respondeu em $SCHEMA_URL"; exit 1; }

# 3) execução da ferramenta
start_ts=$(python3 -c 'import time; print(time.time())')
"tools/run_${TOOL}.sh" || echo "!! ferramenta terminou com erro (ver logs)"
end_ts=$(python3 -c 'import time; print(time.time())')
kill "$spec_srv" 2>/dev/null || true

# 4) logs e uso de memória da API e do proxy (antes de derrubar os contêineres)
"${compose[@]}" logs api > "$OUT_DIR/api.log" 2>&1 || true
for svc in api proxy; do
  cid=$("${compose[@]}" ps -q "$svc" 2>/dev/null || true)
  [ -n "$cid" ] || continue
  s=$(cgroup_mem_stats "$cid")
  registrar_conteiner "$cid" "$svc" "${s%% *}" "${s##* }"
done
"${compose[@]}" down -v --remove-orphans >/dev/null 2>&1 || true

# 5) meta.json (por último: marca a execução como concluída)
python3 - "$OUT_DIR/meta.json.tmp" "$ESTADO_DIR/$run_id.vizinhos" <<PY
import json, os, sys
viz_file = sys.argv[2]
vizinhos = json.load(open(viz_file)) if os.path.exists(viz_file) else []
env = os.environ
json.dump({"run_id": "$run_id", "api": "$API", "tool": "$TOOL", "rep": $REP,
           "seed": $SEED, "budget_sec": $BUDGET_SEC,
           "start_ts": $start_ts, "end_ts": $end_ts,
           "schema_file": "$SCHEMA_FILE",
           "slot": $SLOT, "proxy_port": $PROXY_PORT, "schema_port": $SCHEMA_PORT,
           "slots_paralelos": int(env.get("SLOTS", "1")),
           "vizinhos": vizinhos,
           "limites": {k.lower(): env.get(k, "") for k in
                       ("TOOL_CPUS", "TOOL_MEM", "API_CPUS", "API_MEM", "PROXY_CPUS", "PROXY_MEM", "API_JAVA_OPTS")}},
          open(sys.argv[1], "w"), indent=2)
PY
mv "$OUT_DIR/meta.json.tmp" "$OUT_DIR/meta.json"
echo "=== $run_id concluída ($(date -Is)) ==="
