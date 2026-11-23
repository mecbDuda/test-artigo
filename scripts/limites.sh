#!/usr/bin/env bash
# Calcula os limites de CPU e memória de cada contêiner (API, proxy e ferramenta)
# para N slots paralelos, a partir de nproc e da RAM vista pelo Linux, deixando
# uma reserva para o sistema. Os limites são IGUAIS para todas as ferramentas.
#
#   ./scripts/limites.sh 2        # imprime VAR=valor (usado por scripts/run_parallel.py)
#
# Divisão de cada slot: ferramenta 4/7 das CPUs, API 2/7, proxy 1/7;
# memória: API 1536 MiB, proxy 384 MiB, ferramenta = o resto da fatia do slot.
# O heap das APIs Java é fixado em 75% do limite da API (API_JAVA_OPTS).
set -euo pipefail
SLOTS="${1:-${SLOTS:-2}}"
RESERVA_MEM_MIB="${RESERVA_MEM_MIB:-2048}"   # ~2 GB livres para o sistema
RESERVA_CPUS="${RESERVA_CPUS:-2}"            # 2 CPUs livres para o sistema, o Docker e o orquestrador
API_MEM_MIB="${API_MEM_MIB:-1536}"
PROXY_MEM_MIB="${PROXY_MEM_MIB:-384}"

ncpu=$(nproc)
mem_mib=$(( $(awk '/^MemTotal:/{print $2}' /proc/meminfo) / 1024 ))
fatia_mem=$(( (mem_mib - RESERVA_MEM_MIB) / SLOTS ))
tool_mem=$(( fatia_mem - API_MEM_MIB - PROXY_MEM_MIB ))
[ "$tool_mem" -ge 1024 ] || { echo "limites.sh: memória insuficiente para $SLOTS slots (ferramenta ficaria com ${tool_mem} MiB)" >&2; exit 1; }

python3 - "$ncpu" "$RESERVA_CPUS" "$SLOTS" <<'PY'
import sys
ncpu, res, slots = (int(x) for x in sys.argv[1:])
fatia = (ncpu - res) / slots
print(f"TOOL_CPUS={fatia*4/7:.2f}\nAPI_CPUS={fatia*2/7:.2f}\nPROXY_CPUS={fatia/7:.2f}")
PY
echo "TOOL_MEM=${tool_mem}m"
echo "API_MEM=${API_MEM_MIB}m"
echo "PROXY_MEM=${PROXY_MEM_MIB}m"
echo "API_JAVA_OPTS=-Xmx$(( API_MEM_MIB * 3 / 4 ))m"
echo "HOST_NPROC=$ncpu"
echo "HOST_MEM_MIB=$mem_mib"
echo "SLOTS=$SLOTS"
