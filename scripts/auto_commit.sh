#!/usr/bin/env bash
# Faz commit e push dos dados brutos da campanha à medida que ficam prontos.
# A cada bloco API × repetição concluído (as 3 ferramentas com meta.json), grava
# campaigns.log e data/raw/<api>__*__rep<n>/ num commit e envia ao GitHub.
#   - arquivos > 50 MB: vão comprimidos (<arquivo>.gz); o original fica só no disco
#     local (listado no .gitignore) para a análise;
#   - se o .gz passar de 95 MB, fica fora do commit e é anotado em
#     data/raw/ARQUIVOS_FORA_DO_GIT.txt (docs/desvios.md).
# Uso (na raiz do repositório, normalmente numa janela do tmux):
#   ./scripts/auto_commit.sh            # repete a cada 5 min até a campanha terminar
#   ./scripts/auto_commit.sh --uma-vez  # uma passada só
set -uo pipefail
cd "$(dirname "$0")/.."
set -a; source config/experiment.env; set +a
TOOLS="${TOOLS:-schemathesis restler evomaster}"; APIS="${APIS_CAMPANHA:-$APIS}"; REPS="${REPS:-3}"
FEITOS=data/raw/.blocos_commitados

commit_bloco() {  # <api> <rep>
  local api="$1" rep="$2" d f
  for t in $TOOLS; do
    d="data/raw/${api}__${t}__rep${rep}"
    # arquivos grandes: comprime e mantém o original fora do git
    while IFS= read -r f; do
      [ -f "$f.gz" ] || gzip -k -9 "$f"
      grep -qxF "/$f" .gitignore || echo "/$f" >> .gitignore
      if [ "$(stat -c %s "$f.gz")" -gt $((95 * 1024 * 1024)) ]; then
        grep -qxF "/$f.gz" .gitignore || echo "/$f.gz" >> .gitignore
        grep -qF "$f.gz" data/raw/ARQUIVOS_FORA_DO_GIT.txt 2>/dev/null || \
          echo "$f.gz ($(du -h "$f.gz" | cut -f1) comprimido): acima do limite do GitHub, mantido só no disco local" >> data/raw/ARQUIVOS_FORA_DO_GIT.txt
      fi
    done < <(find "$d" -type f ! -name '*.gz' -size +50M)
    git add -- "$d" 2>/dev/null
  done
  git add .gitignore campaigns.log data/raw/ARQUIVOS_FORA_DO_GIT.txt 2>/dev/null
  git commit -q -m "Campanha: dados brutos de ${api}, repetição ${rep}" && echo "${api} ${rep}" >> "$FEITOS"
  for _ in 1 2 3; do git push -q origin HEAD && break; sleep 30; done
  echo "[auto_commit $(date -Is)] ${api} rep${rep} enviado"
}

while true; do
  for rep in $(seq 1 "$REPS"); do
    for api in $APIS; do
      grep -qxF "${api} ${rep}" "$FEITOS" 2>/dev/null && continue
      ok=1
      for t in $TOOLS; do [ -f "data/raw/${api}__${t}__rep${rep}/meta.json" ] || ok=0; done
      [ "$ok" = 1 ] && commit_bloco "$api" "$rep"
    done
  done
  [ "${1:-}" = "--uma-vez" ] && break
  n=$(wc -l < "$FEITOS" 2>/dev/null || echo 0)
  total=$(( $(echo $APIS | wc -w) * REPS ))
  [ "$n" -ge "$total" ] && { echo "[auto_commit] todos os $total blocos enviados"; break; }
  sleep 300
done
