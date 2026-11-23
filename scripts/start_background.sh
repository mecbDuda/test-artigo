#!/usr/bin/env bash
# Inicia as campanhas completas numa sessão tmux ("campanhas"), gravando a saída
# em campaigns.log na raiz do repositório (o arquivo é acrescentado, não sobrescrito).
#
#   ./scripts/start_background.sh          # inicia (ou retoma) as campanhas
#   tmux attach -t campanhas               # acompanhar ao vivo (sair: Ctrl+b, depois d)
#   tail -f campaigns.log                  # acompanhar pelo log
#
# Retomar após interrupção: rode este script de novo. Execuções com meta.json são
# puladas, e as incompletas vão para data/raw/_incompletas/ e são refeitas.
#
# No WSL: a distribuição é desligada quando nenhum terminal está aberto. Mantenha
# um terminal do Ubuntu aberto ou rode, no PowerShell do Windows:
#   Start-Process wsl.exe -ArgumentList '-d','Ubuntu-24.04','--','sleep','infinity' -WindowStyle Hidden
set -euo pipefail
cd "$(dirname "$0")/.."
if tmux has-session -t campanhas 2>/dev/null; then
  echo "A sessão tmux 'campanhas' já está rodando. Use: tmux attach -t campanhas"
  exit 1
fi
chmod 755 scripts/*.sh tools/*.sh apis/*/*.sh 2>/dev/null || true
tmux new-session -d -s campanhas \
  "bash -c 'echo \"##### início: \$(date -Is)\" >> campaigns.log; ./scripts/run_campaigns.sh 2>&1 | tee -a campaigns.log; echo \"##### fim: \$(date -Is)\" >> campaigns.log'"
echo "Campanhas iniciadas na sessão tmux 'campanhas'. Log: $(pwd)/campaigns.log"
