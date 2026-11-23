#!/usr/bin/env bash
# Prepara e faz commit dos dados brutos da campanha (campaigns.log, data/raw/,
# inclusive recursos.csv e _incompletas/) depois que ela termina.
#   - arquivos > 50 MB: vão comprimidos (<arquivo>.gz); o original fica só no disco
#     local (listado no .gitignore) e é o que a análise usa;
#   - se o .gz passar de 95 MB (o GitHub recusa > 100 MB), ele também fica fora do
#     git e é listado em data/raw/ARQUIVOS_FORA_DO_GIT.txt (anotado em docs/desvios.md).
# Uso (na raiz do repositório):  ./scripts/commit_dados.sh "mensagem do commit"
set -euo pipefail
cd "$(dirname "$0")/.."
msg="${1:-Campanha: dados brutos}"
fora=data/raw/ARQUIVOS_FORA_DO_GIT.txt

while IFS= read -r f; do
  [ -f "$f.gz" ] || gzip -k -9 "$f"
  grep -qxF "/$f" .gitignore || echo "/$f" >> .gitignore
  if [ "$(stat -c %s "$f.gz")" -gt $((95 * 1024 * 1024)) ]; then
    grep -qxF "/$f.gz" .gitignore || echo "/$f.gz" >> .gitignore
    grep -qF "$f.gz" "$fora" 2>/dev/null || \
      echo "$f ($(du -h "$f" | cut -f1); $(du -h "$f.gz" | cut -f1) comprimido): acima do limite do GitHub, mantido só no disco local" >> "$fora"
  fi
done < <(find data/raw -type f ! -name '*.gz' -size +50M | sort)

git add .gitignore campaigns.log data/raw
git commit -q -m "$msg" && git push -q origin HEAD
echo "Commit e push feitos. Arquivos fora do git: $( [ -f "$fora" ] && wc -l < "$fora" || echo 0 )"
