#!/usr/bin/env bash
# Executa o Schemathesis durante BUDGET_SEC segundos.
# Variáveis: SCHEMA_URL BASE_URL OUT_DIR BUDGET_SEC SEED [AUTH_HEADER] [ST_VERSION]
#
# O Schemathesis termina quando esgota os exemplos que gera; para usar todo o
# orçamento, ele é reexecutado com sementes diferentes até o tempo acabar.
#
# ATENÇÃO: confira os parâmetros na versão fixada antes da primeira campanha:
#   docker run --rm schemathesis/schemathesis:$ST_VERSION run --help
set -euo pipefail
source "$(dirname "$0")/lib.sh"
ST_VERSION="${ST_VERSION:-stable}"

auth_args=()
[ -n "${AUTH_HEADER:-}" ] && auth_args=(--header "$AUTH_HEADER")

end=$((SECONDS + BUDGET_SEC)); i=0
while [ "$SECONDS" -lt "$end" ]; do
  remaining=$((end - SECONDS))
  mkdir -p "$OUT_DIR/iter_$i"
  run_limited "st_$i" "$remaining" \
    -v "$OUT_DIR/iter_$i:/out" \
    "schemathesis/schemathesis:$ST_VERSION" run "$SCHEMA_URL" \
      --url "$BASE_URL" \
      --checks all \
      --seed "$((SEED + i))" \
      --report junit --report-dir /out \
      ${auth_args[@]+"${auth_args[@]}"}
  i=$((i + 1))
done
echo "schemathesis: $i execução(ões) dentro do orçamento" > "$OUT_DIR/tool_summary.txt"
