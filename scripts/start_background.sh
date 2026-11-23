#!/usr/bin/env bash
# Inicia (ou RETOMA) a campanha em paralelo numa sessão tmux ("campanhas"),
# acrescentando a saída em campaigns.log na raiz do repositório.
#
#   ./scripts/start_background.sh          # inicia ou retoma (SLOTS=2 por padrão)
#   ./scripts/progress.sh                  # progresso
#   tmux attach -t campanhas               # ao vivo (sair sem parar: Ctrl+b, depois d)
#   touch PAUSAR                           # pausa segura: termina as execuções em andamento e para
#
# Retomar depois de uma pausa ou de desligar o computador: rode este script de novo.
# Ele apaga o arquivo PAUSAR, se existir. Execuções concluídas (com meta.json) são
# puladas, e as incompletas vão para data/raw/_incompletas/ e são refeitas.
#
# No WSL: a distribuição desliga quando nenhum processo do Windows a mantém aberta.
# Deixe um terminal do Ubuntu aberto ou rode, no PowerShell do Windows:
#   Start-Process wsl.exe -ArgumentList '-d','Ubuntu-24.04','--','sleep','infinity' -WindowStyle Hidden
set -euo pipefail
cd "$(dirname "$0")/.."
if tmux has-session -t campanhas 2>/dev/null; then
  echo "A sessão tmux 'campanhas' já está rodando. Use: tmux attach -t campanhas"
  exit 1
fi
if [ -f PAUSAR ]; then rm -f PAUSAR; echo "Arquivo PAUSAR removido: retomando a campanha."; fi
chmod 755 scripts/*.sh scripts/*.py tools/*.sh apis/*/*.sh analysis/*.py 2>/dev/null || true
export SLOTS="${SLOTS:-2}"
tmux new-session -d -s campanhas -e SLOTS="$SLOTS" \
  "bash -c 'echo \"##### início: \$(date -Is)\" >> campaigns.log; python3 -u scripts/run_parallel.py 2>&1 | tee -a campaigns.log; echo \"##### fim: \$(date -Is)\" >> campaigns.log'"
echo "Campanha iniciada na sessão tmux 'campanhas' com $SLOTS slots. Log: $(pwd)/campaigns.log"
