#!/usr/bin/env bash
# Executa todas as campanhas: REPS repetições × APIS × TOOLS.
# Uso (na raiz do repositório):
#   ./scripts/run_campaigns.sh                      # usa config/experiment.env
#   BUDGET_MIN=2 REPS=1 APIS=vampi ./scripts/run_campaigns.sh   # teste rápido
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
# Variáveis passadas na linha de comando têm precedência sobre config/experiment.env
# (na versão original o arquivo as sobrescrevia, e o "teste rápido" rodava com o
# orçamento completo; ver docs/desvios.md, D07).
_cli_overrides=()
for _v in TOOLS APIS REPS BUDGET_MIN BASE_SEED ST_VERSION RESTLER_IMAGE EM_VERSION; do
  [ -n "${!_v+x}" ] && _cli_overrides+=("$_v=${!_v}")
done
[ -f config/experiment.env ] && set -a && source config/experiment.env && set +a
for _kv in ${_cli_overrides[@]+"${_cli_overrides[@]}"}; do export "$_kv"; done
echo ">> TOOLS=[$TOOLS] APIS=[$APIS] REPS=$REPS BUDGET_MIN=$BUDGET_MIN BASE_SEED=$BASE_SEED"

TOOLS="${TOOLS:-schemathesis restler evomaster}"
APIS="${APIS:-vampi}"
REPS="${REPS:-3}"
BUDGET_MIN="${BUDGET_MIN:-30}"
BASE_SEED="${BASE_SEED:-1000}"
SCHEMA_PORT="${SCHEMA_PORT:-8099}"
export BUDGET_SEC=$((BUDGET_MIN * 60))

for rep in $(seq 1 "$REPS"); do
  for api in $APIS; do
    # alterna a ordem das ferramentas a cada repetição (reduz efeito de ordem)
    order=$(echo $TOOLS | tr ' ' '\n' | python3 -c "import sys,random; t=sys.stdin.read().split(); random.Random($rep).shuffle(t); print(' '.join(t))")
    for tool in $order; do
      ( set -a; source "apis/$api/api.env"; set +a
        run_id="${api}__${tool}__rep${rep}"
        export OUT_DIR="$ROOT/data/raw/$run_id"
        export LOG_DIR="$OUT_DIR"
        export SEED=$((BASE_SEED + rep))
        export SCHEMA_PATH="$ROOT/$SCHEMA_FILE"
        export SCHEMA_URL="http://localhost:$SCHEMA_PORT/$(basename "$SCHEMA_FILE")"
        export BASE_URL
        # só conta como concluída a execução que gravou meta.json; uma execução
        # interrompida é movida (não apagada) para data/raw/_incompletas/ e refeita
        if [ -f "$OUT_DIR/meta.json" ]; then echo ">> $run_id já concluída, pulando"; exit 0; fi
        if [ -d "$OUT_DIR" ]; then
          mkdir -p "$ROOT/data/raw/_incompletas"
          mv "$OUT_DIR" "$ROOT/data/raw/_incompletas/${run_id}__$(date +%Y%m%dT%H%M%S)"
          echo ">> $run_id estava incompleta; movida para data/raw/_incompletas/ e será refeita"
        fi
        mkdir -p "$OUT_DIR"
        echo "=== $run_id ($(date -Is)) ==="

        compose=(docker compose -p fuzzexp -f "apis/$api/docker-compose.yml")
        # 1) estado limpo: derruba tudo (inclusive volumes) e sobe de novo
        "${compose[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
        # (o subshell roda sob "|| echo", então set -e não vale aqui: erros são tratados explicitamente)
        "${compose[@]}" up -d || { echo "!! docker compose up falhou"; exit 1; }
        healthy=0
        for _ in $(seq 1 90); do curl -fsS -o /dev/null "$HEALTH_URL" && { healthy=1; break; }; sleep 2; done
        [ "$healthy" = 1 ] || { echo "!! API não respondeu em $HEALTH_URL"; "${compose[@]}" down -v >/dev/null 2>&1; exit 1; }
        # o reset pode falhar de forma intermitente (ex.: no VAmPI, /createdb sorteia
        # títulos de livro únicos e às vezes colide); tenta de novo antes de desistir
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
        python3 -m http.server "$SCHEMA_PORT" -d "$(dirname "$SCHEMA_PATH")" >/dev/null 2>&1 &
        spec_srv=$!
        for _ in $(seq 1 20); do curl -fsS -o /dev/null "$SCHEMA_URL" && break; sleep 0.5; done

        # 3) metadados + execução
        start_ts=$(python3 -c 'import time; print(time.time())')
        "tools/run_${tool}.sh" || echo "!! ferramenta terminou com erro (ver logs)"
        end_ts=$(python3 -c 'import time; print(time.time())')
        kill "$spec_srv" 2>/dev/null || true

        python3 - "$OUT_DIR/meta.json" <<PY
import json, sys
json.dump({"run_id": "$run_id", "api": "$api", "tool": "$tool", "rep": $rep,
           "seed": $SEED, "budget_sec": $BUDGET_SEC,
           "start_ts": $start_ts, "end_ts": $end_ts,
           "schema_file": "$SCHEMA_FILE"}, open(sys.argv[1], "w"), indent=2)
PY
        # 4) logs da API (stack traces ajudam a deduplicar e validar)
        "${compose[@]}" logs api > "$OUT_DIR/api.log" 2>&1 || true
        "${compose[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
      ) || echo "!! ${api}__${tool}__rep${rep} falhou (sem meta.json); será refeita ao rodar o script de novo"
    done
  done
done
echo "Concluído. Próximo passo: python3 analysis/extract_findings.py"
