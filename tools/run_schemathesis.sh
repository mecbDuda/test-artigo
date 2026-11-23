#!/usr/bin/env bash
# Executa o Schemathesis durante BUDGET_SEC segundos.
# Variáveis: SCHEMA_URL BASE_URL OUT_DIR BUDGET_SEC SEED [AUTH_HEADER] [ST_VERSION]
#
# Desde a 4.x o Schemathesis aceita --max-time: as fases de fuzzing e stateful
# se repetem até o orçamento acabar, e o relatório é gravado ao final. O laço
# abaixo só reexecuta (com outra semente) se a ferramenta terminar antes do tempo.
# O contêiner recebe 30 s de folga além de --max-time para gravar o relatório.
#
# Parâmetros conferidos com `run --help` da 4.34.0 (ver docs/desvios.md).
set -euo pipefail
source "$(dirname "$0")/lib.sh"
ST_VERSION="${ST_VERSION:-stable}"

auth_args=()
[ -n "${AUTH_HEADER:-}" ] && auth_args=(--header "$AUTH_HEADER")

end=$((SECONDS + BUDGET_SEC)); i=0
while [ "$SECONDS" -lt "$end" ]; do
  remaining=$((end - SECONDS))
  it_start=$SECONDS
  mkdir -p "$OUT_DIR/iter_$i"
  # a imagem roda com usuário não-root; usa o mesmo usuário do host para poder
  # gravar o relatório no volume (docs/desvios.md, D12)
  run_limited "st_$i" "$((remaining + 30))" \
    --user "$(id -u):$(id -g)" \
    -v "$OUT_DIR/iter_$i:/out" \
    "schemathesis/schemathesis:$ST_VERSION" run "$SCHEMA_URL" \
      --url "$BASE_URL" \
      --checks all \
      --seed "$((SEED + i))" \
      --max-time "$remaining" \
      --report junit --report-dir /out \
      ${auth_args[@]+"${auth_args[@]}"}
  i=$((i + 1))
  # proteção: se a ferramenta falha logo de cara, não fica num laço de reinícios
  if [ $((SECONDS - it_start)) -lt 10 ]; then
    echo "schemathesis: iteração $((i - 1)) durou menos de 10 s; interrompendo o laço" >> "$OUT_DIR/tool_summary.txt"
    break
  fi
done
echo "schemathesis: $i execução(ões) dentro do orçamento" >> "$OUT_DIR/tool_summary.txt"
