#!/usr/bin/env bash
# Mostra o progresso da campanha: execuções concluídas, em andamento (por slot),
# estado da pausa, estimativa do tempo restante e os últimos erros do log.
cd "$(dirname "$0")/.."
[ -f config/experiment.env ] && set -a && source config/experiment.env && set +a
SLOTS="${SLOTS:-2}"
total=$(( $(echo $TOOLS | wc -w) * $(echo $APIS | wc -w) * REPS ))
done_n=$(ls data/raw/*__*__rep*/meta.json 2>/dev/null | wc -l)
echo "Concluídas: $done_n de $total  (orçamento: $BUDGET_MIN min por execução, $SLOTS slots)"
if tmux has-session -t campanhas 2>/dev/null; then echo "Sessão tmux 'campanhas': rodando"; else echo "Sessão tmux 'campanhas': parada"; fi
[ -f PAUSAR ] && echo "PAUSAR existe: nenhuma execução nova será iniciada (aguardando as em andamento)"
if [ -f data/raw/.estado/em_andamento.json ]; then
  echo "Em andamento:"; python3 -c 'import json; [print(f"  slot {k}: {v}") for k, v in json.load(open("data/raw/.estado/em_andamento.json")).items()]'
fi
left=$(( total - done_n ))
mins=$(( (left * (BUDGET_MIN + 3) + SLOTS - 1) / SLOTS ))
echo "Estimativa restante: ~$(( mins / 60 )) h $(( mins % 60 )) min"
grep -E 'PAUSADO|CONCLUÍDA|NÃO concluídas' campaigns.log 2>/dev/null | tail -2
grep -E '!!' campaigns.log 2>/dev/null | tail -5
