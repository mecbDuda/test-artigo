#!/usr/bin/env bash
# Faz login no VAmPI e imprime o cabeçalho de autenticação.
# Confira usuário/senha padrão no README do VAmPI (populados por /createdb).
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:8080}"
USER_NAME="${VAMPI_USER:-name1}"
USER_PASS="${VAMPI_PASS:-pass1}"

token=$(curl -fsS -X POST "$BASE_URL/users/v1/login" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$USER_NAME\",\"password\":\"$USER_PASS\"}" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["auth_token"])')

echo "Authorization: Bearer $token"
