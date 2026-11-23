#!/usr/bin/env bash
# Executa o RESTler: compile -> test (smoke) -> fuzz, com o orçamento restante.
# Variáveis: SCHEMA_PATH BASE_URL OUT_DIR BUDGET_SEC SEED [AUTH_HEADER] [RESTLER_IMAGE]
#
# Versão usada: v9.2.4 (a v8.5.0 quebrava no modo fuzz; ver docs/desvios.md, D11).
# Caminho do binário conferido na imagem: /RESTler/restler/Restler.dll
set -euo pipefail
source "$(dirname "$0")/lib.sh"
RESTLER_IMAGE="${RESTLER_IMAGE:-mcr.microsoft.com/restlerfuzzer/restler:v9.2.4}"
RESTLER_BIN="${RESTLER_BIN:-dotnet /RESTler/restler/Restler.dll}"

host_port="${BASE_URL#http://}"; host="${host_port%%:*}"; port="${host_port##*:}"; port="${port%%/*}"
[ "$host" = "localhost" ] && host="127.0.0.1"

cp "$SCHEMA_PATH" "$OUT_DIR/spec.${SCHEMA_PATH##*.}"
spec_in="/work/spec.${SCHEMA_PATH##*.}"

# Autenticação: o RESTler executa um comando que imprime {u'app': {}} + cabeçalho
auth_args=""
if [ -n "${AUTH_HEADER:-}" ]; then
  printf "{u'app': {}}\n%s\n" "$AUTH_HEADER" > "$OUT_DIR/token.txt"
  auth_args="--token_refresh_command 'cat /work/token.txt' --token_refresh_interval 3600"
fi

start=$SECONDS
# 1) compile
docker run --rm --network host -v "$OUT_DIR:/work" -w /work --entrypoint sh "$RESTLER_IMAGE" \
  -c "$RESTLER_BIN compile --api_spec $spec_in" > "$OUT_DIR/restler_compile.log" 2>&1

# fixa a semente aleatória nas configurações do motor.
# Se o caminho base compilado for "/" (ex.: Swagger 2.0 com basePath "/"), o RESTler
# gera URLs com barra dupla ("//config"); a opção "basepath" do motor o substitui
# por "" sem alterar a especificação (docs/desvios.md, D13).
python3 - "$OUT_DIR/Compile/engine_settings.json" "$SEED" "$OUT_DIR/Compile/grammar.py" <<'PY'
import json, sys
p, seed, grammar = sys.argv[1], int(sys.argv[2]), sys.argv[3]
s = json.load(open(p)); s["random_seed"] = seed
if 'restler_basepath("/")' in open(grammar, encoding="utf-8").read():
    s["basepath"] = ""
json.dump(s, open(p, "w"), indent=2)
PY

common="--grammar_file /work/Compile/grammar.py --dictionary_file /work/Compile/dict.json \
 --settings /work/Compile/engine_settings.json --no_ssl --target_ip $host --target_port $port $auth_args"

# 2) test (smoke): mede cobertura inicial de requisições
docker run --rm --network host -v "$OUT_DIR:/work" -w /work --entrypoint sh "$RESTLER_IMAGE" \
  -c "$RESTLER_BIN test $common" > "$OUT_DIR/restler_test.log" 2>&1 || true

# 3) fuzz com o tempo restante (o RESTler recebe o orçamento em horas)
remaining=$((BUDGET_SEC - (SECONDS - start)))
hours=$(python3 -c "print(round(max($remaining,60)/3600, 4))")
run_limited "restler" "$((remaining + 60))" -v "$OUT_DIR:/work" -w /work --entrypoint sh "$RESTLER_IMAGE" \
  -c "$RESTLER_BIN fuzz $common --time_budget $hours"
