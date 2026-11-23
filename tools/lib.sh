#!/usr/bin/env bash
# Funções comuns aos wrappers das ferramentas.

# run_limited <nome-do-container> <segundos> <args do docker run...>
# Executa um contêiner e o encerra quando o orçamento de tempo acaba.
run_limited() {
  local name="$1" secs="$2"; shift 2
  docker rm -f "$name" >/dev/null 2>&1 || true
  docker run -d --name "$name" --network host "$@" >/dev/null
  local waited=0
  while [ "$waited" -lt "$secs" ]; do
    if [ "$(docker inspect -f '{{.State.Running}}' "$name" 2>/dev/null)" != "true" ]; then
      break
    fi
    sleep 2; waited=$((waited + 2))
  done
  docker logs "$name" > "$OUT_DIR/tool_stdout_${name}.log" 2>&1 || true
  docker rm -f "$name" >/dev/null 2>&1 || true
}
