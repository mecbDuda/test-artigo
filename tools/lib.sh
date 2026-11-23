#!/usr/bin/env bash
# Funções comuns aos wrappers das ferramentas.
#
# Execução em paralelo (scripts/run_parallel.py): cada slot define
#   CONTAINER_SUFFIX  sufixo único dos nomes de contêiner (ex.: "_s1")
#   TOOL_CPUS/TOOL_MEM  limites do contêiner da ferramenta (iguais para todas)
# Sem essas variáveis (execução isolada), os contêineres rodam sem sufixo e sem limite.

# Lê, no cgroup do contêiner em execução, o pico de memória e quantas vezes o
# limite foi atingido. Imprime "<pico_bytes> <vezes_no_limite>" (ou "NA NA").
cgroup_mem_stats() {
  local id="$1" d peak="NA" hits="NA"
  for d in "/sys/fs/cgroup/memory/docker/$id" "/sys/fs/cgroup/memory/system.slice/docker-$id.scope"; do
    if [ -r "$d/memory.max_usage_in_bytes" ]; then          # cgroup v1
      peak=$(cat "$d/memory.max_usage_in_bytes"); hits=$(cat "$d/memory.failcnt"); break
    fi
  done
  if [ "$peak" = "NA" ]; then
    for d in "/sys/fs/cgroup/system.slice/docker-$id.scope" "/sys/fs/cgroup/docker/$id"; do
      if [ -r "$d/memory.peak" ]; then                       # cgroup v2
        peak=$(cat "$d/memory.peak"); hits=$(awk '$1=="max"{print $2}' "$d/memory.events"); break
      fi
    done
  fi
  echo "$peak $hits"
}

# registrar_conteiner <nome-docker> <papel> <pico> <vezes_no_limite>
# Acrescenta uma linha a $OUT_DIR/conteineres.tsv com limites, pico de memória,
# OOM e código de saída (o contêiner precisa existir, parado ou não).
registrar_conteiner() {
  local name="$1" papel="$2" peak="$3" hits="$4" f="$OUT_DIR/conteineres.tsv"
  [ -f "$f" ] || printf 'conteiner\tpapel\tnano_cpus\tmem_limite_bytes\tmem_pico_bytes\tvezes_no_limite\toom_killed\tcodigo_saida\n' > "$f"
  docker inspect -f "{{.Name}}	$papel	{{.HostConfig.NanoCpus}}	{{.HostConfig.Memory}}	$peak	$hits	{{.State.OOMKilled}}	{{.State.ExitCode}}" "$name" 2>/dev/null \
    | sed -E 's#^/##' >> "$f" || true
}

# argumentos de limite do contêiner da ferramenta (vazios fora do modo paralelo)
tool_limit_args() {
  [ -n "${TOOL_CPUS:-}" ] && printf -- '--cpus\n%s\n' "$TOOL_CPUS"
  [ -n "${TOOL_MEM:-}" ] && printf -- '--memory\n%s\n' "$TOOL_MEM"
  return 0
}

# run_limited <nome-lógico> <segundos> <args do docker run...>
# Executa um contêiner e o encerra quando o orçamento de tempo acaba.
# O contêiner se chama <nome-lógico>$CONTAINER_SUFFIX; a saída vai para
# $OUT_DIR/${LOG_NAME:-tool_stdout_<nome-lógico>.log}.
run_limited() {
  local name="$1" secs="$2"; shift 2
  local cname="${name}${CONTAINER_SUFFIX:-}" id peak="NA" hits="NA" s
  local -a lim; mapfile -t lim < <(tool_limit_args)
  docker rm -f "$cname" >/dev/null 2>&1 || true
  id=$(docker run -d --name "$cname" --network host ${lim[@]+"${lim[@]}"} "$@")
  local waited=0
  while [ "$waited" -lt "$secs" ]; do
    if [ "$(docker inspect -f '{{.State.Running}}' "$cname" 2>/dev/null)" != "true" ]; then
      break
    fi
    s=$(cgroup_mem_stats "$id"); [ "${s%% *}" != "NA" ] && { peak="${s%% *}"; hits="${s##* }"; }
    sleep 2; waited=$((waited + 2))
  done
  s=$(cgroup_mem_stats "$id"); [ "${s%% *}" != "NA" ] && { peak="${s%% *}"; hits="${s##* }"; }
  docker logs "$cname" > "$OUT_DIR/${LOG_NAME:-tool_stdout_${name}.log}" 2>&1 || true
  # SIGKILL ao fim do orçamento, como o "docker rm -f" original (sem folga extra);
  # o contêiner parado ainda existe para registrar OOM e código de saída
  docker kill "$cname" >/dev/null 2>&1 || true
  registrar_conteiner "$cname" "ferramenta:$name" "$peak" "$hits"
  docker rm -f "$cname" >/dev/null 2>&1 || true
}
