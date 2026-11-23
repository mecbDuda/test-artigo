#!/usr/bin/env bash
# Executa o EvoMaster em modo CAIXA-PRETA durante BUDGET_SEC segundos.
# Variáveis: SCHEMA_URL BASE_URL OUT_DIR BUDGET_SEC SEED [AUTH_HEADER] [EM_VERSION]
#
# Versão fixada em v5.x, que usa --bbSwaggerUrl/--bbTargetUrl. Na série 6.x o
# parâmetro passou a ser --schema/--base; ajuste se mudar a versão.
#   docker run --rm webfuzzing/evomaster:$EM_VERSION --help
set -euo pipefail
source "$(dirname "$0")/lib.sh"
EM_VERSION="${EM_VERSION:-v5.1.0}"

auth_args=()
[ -n "${AUTH_HEADER:-}" ] && auth_args=(--header0 "$AUTH_HEADER")

mkdir -p "$OUT_DIR/generated_tests"
run_limited "evomaster" "$((BUDGET_SEC + 120))" \
  -v "$OUT_DIR/generated_tests:/generated_tests" \
  "webfuzzing/evomaster:$EM_VERSION" \
    --blackBox true \
    --bbSwaggerUrl "$SCHEMA_URL" \
    --bbTargetUrl "$BASE_URL" \
    --maxTime "${BUDGET_SEC}s" \
    --seed "$SEED" \
    --outputFormat JAVA_JUNIT_5 \
    ${auth_args[@]+"${auth_args[@]}"}
