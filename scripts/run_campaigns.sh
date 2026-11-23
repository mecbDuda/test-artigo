#!/usr/bin/env bash
# Executa a campanha em primeiro plano, sem tmux (atalho para scripts/run_parallel.py).
#   ./scripts/run_campaigns.sh                                   # usa config/experiment.env, 2 slots
#   SLOTS=1 ./scripts/run_campaigns.sh                           # uma execução por vez
#   BUDGET_MIN=2 REPS=1 ./scripts/run_campaigns.sh               # teste rápido
# Variáveis da linha de comando têm precedência sobre config/experiment.env (D07).
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 -u scripts/run_parallel.py "$@"
