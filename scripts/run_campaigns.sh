#!/usr/bin/env bash
# Executa todas as campanhas: REPS repetições × APIS × TOOLS.
# Uso (na raiz do repositório):
#   ./scripts/run_campaigns.sh                      # usa config/experiment.env
#   BUDGET_MIN=2 REPS=1 APIS=vampi ./scripts/run_campaigns.sh   # teste rápido
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
[ -f config/experiment.env ] && set -a && source config/experiment.env && set +a

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
        if [ -d "$OUT_DIR" ]; then echo ">> $run_id já existe, pulando"; exit 0; fi
        mkdir -p "$OUT_DIR"
        echo "=== $run_id ($(date -Is)) ==="

        compose=(docker compose -p fuzzexp -f "apis/$api/docker-compose.yml")
        # 1) estado limpo: derruba tudo (inclusive volumes) e sobe de novo
        "${compose[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
        "${compose[@]}" up -d
        for _ in $(seq 1 90); do curl -fsS -o /dev/null "$HEALTH_URL" && break; sleep 2; done
        eval "$INIT_CMD" >/dev/null
        AUTH_HEADER=""
        [ -n "${AUTH_SCRIPT:-}" ] && AUTH_HEADER="$(bash "$AUTH_SCRIPT")"
        export AUTH_HEADER
        # descarta as requisições feitas pelo próprio script de preparação
        : > "$OUT_DIR/flows.jsonl"

        # 2) servidor estático com a especificação (mesmo arquivo para todas as ferramentas)
        python3 -m http.server "$SCHEMA_PORT" -d "$(dirname "$SCHEMA_PATH")" >/dev/null 2>&1 &
        spec_srv=$!

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
      )
    done
  done
done
echo "Concluído. Próximo passo: python3 analysis/extract_findings.py"
