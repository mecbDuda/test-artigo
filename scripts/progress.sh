#!/usr/bin/env bash
# Mostra o progresso das campanhas: execuções concluídas (com meta.json) e a atual.
cd "$(dirname "$0")/.."
[ -f config/experiment.env ] && set -a && source config/experiment.env && set +a
total=$(( $(echo $TOOLS | wc -w) * $(echo $APIS | wc -w) * REPS ))
done_n=$(ls data/raw/*__*__rep*/meta.json 2>/dev/null | wc -l)
echo "Concluídas: $done_n de $total  (orçamento: $BUDGET_MIN min por execução)"
cur=$(grep -E '^=== ' campaigns.log 2>/dev/null | tail -1)
[ -n "$cur" ] && echo "Última iniciada: $cur"
left=$(( total - done_n ))
echo "Estimativa restante: ~$(( left * (BUDGET_MIN + 2) / 60 )) h $(( left * (BUDGET_MIN + 2) % 60 )) min"
grep -E '^!!' campaigns.log 2>/dev/null | tail -5
