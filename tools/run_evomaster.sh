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

# O EvoMaster acrescenta sozinho o caminho dos "servers"/basePath da especificação;
# por isso recebe só a origem (esquema://host:porta) de BASE_URL. Com a URL completa,
# no petclinic-rest ele chamava /petclinic/petclinic/... (docs/desvios.md, D14).
target_origin="$(printf '%s' "$BASE_URL" | sed -E 's#^(https?://[^/]+).*#\1#')"

mkdir -p "$OUT_DIR/generated_tests"
# Folga de 600 s depois do orçamento de busca (--maxTime): a minimização tem limite
# padrão de 5 min (--minimizeTimeout, v5.1.0) e o relatório WFC só é gravado depois
# dela. Com 120 s de folga, na catwatch o contêiner era morto durante a minimização
# e o report.json se perdia (docs/desvios.md, D18).
run_limited "evomaster" "$((BUDGET_SEC + 600))" \
  -v "$OUT_DIR/generated_tests:/generated_tests" \
  "webfuzzing/evomaster:$EM_VERSION" \
    --blackBox true \
    --bbSwaggerUrl "$SCHEMA_URL" \
    --bbTargetUrl "$target_origin" \
    --maxTime "${BUDGET_SEC}s" \
    --seed "$SEED" \
    --outputFormat JAVA_JUNIT_5 \
    --outputFolder /generated_tests \
    ${auth_args[@]+"${auth_args[@]}"}
