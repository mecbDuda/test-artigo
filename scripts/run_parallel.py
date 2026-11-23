#!/usr/bin/env python3
"""
Executa a campanha em N slots paralelos isolados (scripts/run_one.sh em cada slot).

  python3 scripts/run_parallel.py                 # usa config/experiment.env e SLOTS=2
  SLOTS=2 BUDGET_MIN=2 REPS=1 python3 scripts/run_parallel.py   # teste rápido

O que faz:
- monta a fila de execuções (REPS × APIS × TOOLS) intercalando ferramentas e APIs:
  itens vizinhos na fila diferem em ferramenta e em API, e a ordem muda a cada
  repetição; ao escolher a próxima execução, evita (se der) a ferramenta que já
  está rodando no outro slot. Assim nenhuma ferramenta roda sempre com os mesmos
  vizinhos;
- pula execuções concluídas (com meta.json) e, ao iniciar, move as incompletas
  (pasta sem meta.json) para data/raw/_incompletas/ para refazê-las;
- grava no meta.json de cada execução o slot e as execuções vizinhas (que rodaram
  ao mesmo tempo em outros slots);
- PAUSA SEGURA: se existir o arquivo PAUSAR na raiz do repositório, não inicia
  novas execuções, espera as que estão rodando terminarem e encerra com
  "PAUSADO COM SEGURANÇA – pode desligar";
- registra uso de CPU e memória (máquina e cada contêiner) a cada minuto em
  data/raw/recursos.csv;
- registra pausas, retomadas e execuções refeitas em docs/desvios.md.
"""
import json
import os
import random
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
RAW = os.path.join(ROOT, "data", "raw")
ESTADO = os.path.join(RAW, ".estado")
PAUSAR = os.path.join(ROOT, "PAUSAR")
REGISTRO = os.environ.get("REGISTRO_DESVIOS", os.path.join(ROOT, "docs", "desvios.md"))
RECURSOS = os.environ.get("RECURSOS_CSV", os.path.join(RAW, "recursos.csv"))
MAX_TENTATIVAS = 3          # por execução, dentro de uma mesma sessão
POLL = 5                    # segundos entre verificações
REG_HEADER = ("\n## Registro automático da campanha (pausas, retomadas e execuções refeitas)\n\n"
              "Gerado por `scripts/run_parallel.py` e `scripts/run_one.sh`.\n\n"
              "| Data | Evento | Detalhe |\n|---|---|---|\n")

_print_lock = threading.Lock()


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def log(msg):
    with _print_lock:
        print(f"[{now()}] {msg}", flush=True)


def registrar(evento, detalhe):
    with open(REGISTRO, "a", encoding="utf-8") as f:
        f.write(f"| {now()} | {evento} | {detalhe} |\n")


def load_config():
    """experiment.env, com precedência das variáveis passadas na linha de comando (D07)."""
    keys = ["TOOLS", "APIS", "REPS", "BUDGET_MIN", "BASE_SEED", "ST_VERSION", "RESTLER_IMAGE", "EM_VERSION", "SLOTS"]
    cli = {k: os.environ[k] for k in keys if k in os.environ}
    out = subprocess.run(["bash", "-c", "set -a; source config/experiment.env; set +a; env -0"],
                         capture_output=True, check=True).stdout.decode()
    cfg = dict(kv.split("=", 1) for kv in out.split("\0") if "=" in kv)
    cfg.update(cli)
    return cfg


def limites(slots):
    out = subprocess.run(["bash", "scripts/limites.sh", str(slots)], capture_output=True, text=True, check=True).stdout
    return dict(l.split("=", 1) for l in out.strip().splitlines())


def montar_fila(tools, apis, reps, base_seed):
    """Para cada repetição, as 9 combinações em ordem tal que itens vizinhos diferem
    em ferramenta e em API (quadrado latino); rótulos embaralhados por repetição."""
    fila = []
    for rep in range(1, reps + 1):
        rng = random.Random(base_seed + rep)
        t = tools[:]; a = apis[:]
        rng.shuffle(t); rng.shuffle(a)
        combos = []
        for j in range(len(t) * len(a)):
            ti = j % len(t)
            ai = (j // len(t) + j) % len(a)
            combos.append((a[ai], t[ti]))
        # garante todas as combinações mesmo se len(tools) != len(apis)
        todas = [(x, y) for x in a for y in t]
        combos = list(dict.fromkeys(combos + todas))
        fila += [(api, tool, rep) for api, tool in combos]
    return fila


def run_id(item):
    api, tool, rep = item
    return f"{api}__{tool}__rep{rep}"


def concluida(item):
    return os.path.exists(os.path.join(RAW, run_id(item), "meta.json"))


def mover_incompleta(rid, motivo):
    src = os.path.join(RAW, rid)
    if not os.path.isdir(src):
        return
    os.makedirs(os.path.join(RAW, "_incompletas"), exist_ok=True)
    dest_name = f"{rid}__{datetime.now().strftime('%Y%m%dT%H%M%S')}"
    os.rename(src, os.path.join(RAW, "_incompletas", dest_name))
    registrar("execução refeita", f"`{rid}` {motivo}; movida para `data/raw/_incompletas/{dest_name}`")
    log(f"{rid} {motivo}; movida para data/raw/_incompletas/{dest_name} e será refeita")


def limpar_restos(max_slots=8):
    """Remove contêineres e redes de slots que sobraram de uma interrupção brusca."""
    for k in range(max_slots):
        proj = f"fuzzexp_{k}"
        sh = (f"docker ps -aq --filter label=com.docker.compose.project={proj} | xargs -r docker rm -f; "
              f"docker ps -aq --filter 'name=_s{k}$' | xargs -r docker rm -f; "
              f"docker network ls -q --filter label=com.docker.compose.project={proj} | xargs -r docker network rm")
        subprocess.run(["bash", "-c", sh], capture_output=True)


def gravar_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)


# ----------------------------------------------------------------- monitor de recursos
class Monitor(threading.Thread):
    COLS = ["data_hora", "escopo", "nome", "slot", "execucao", "cpu_pct", "mem_mib", "mem_limite_mib", "mem_pct"]

    def __init__(self, em_andamento):
        super().__init__(daemon=True)
        self.em_andamento = em_andamento   # slot -> run_id (lido sem lock; só leitura)
        self.parar = threading.Event()
        self._cpu_prev = self._cpu()

    @staticmethod
    def _cpu():
        v = [int(x) for x in open("/proc/stat").readline().split()[1:]]
        idle = v[3] + v[4]
        return sum(v), idle

    @staticmethod
    def _mib(s):
        s = s.strip()
        mult = {"B": 1 / 1048576, "KiB": 1 / 1024, "kB": 1 / 1024, "MiB": 1, "MB": 1, "GiB": 1024, "GB": 1024, "TiB": 1048576}
        for u in sorted(mult, key=len, reverse=True):
            if s.endswith(u):
                return round(float(s[: -len(u)]) * mult[u], 1)
        return ""

    def amostra(self):
        rows = []
        tot, idle = self._cpu()
        pt, pi = self._cpu_prev
        self._cpu_prev = (tot, idle)
        cpu = round(100 * (1 - (idle - pi) / max(tot - pt, 1)), 1)
        mi = {l.split(":")[0]: int(l.split()[1]) for l in open("/proc/meminfo")}
        used = (mi["MemTotal"] - mi["MemAvailable"]) / 1024
        rows.append([now(), "maquina", "host", "", "", cpu, round(used, 1), round(mi["MemTotal"] / 1024, 1),
                     round(100 * used * 1024 / mi["MemTotal"], 1)])
        try:
            out = subprocess.run(["docker", "stats", "--no-stream", "--format",
                                  "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"],
                                 capture_output=True, text=True, timeout=50).stdout
        except subprocess.TimeoutExpired:
            out = ""
        for line in out.strip().splitlines():
            name, cpu_s, mem_s, memp = line.split("\t")
            slot = ""
            if name.startswith("fuzzexp_"):
                slot = name.split("_")[1].split("-")[0]
            elif "_s" in name:
                slot = name.rsplit("_s", 1)[1]
            usage, _, limit = mem_s.partition(" / ")
            rows.append([now(), "conteiner", name, slot, (self.em_andamento.get(int(slot)) or "") if slot.isdigit() else "",
                         cpu_s.rstrip("%"), self._mib(usage), self._mib(limit), memp.rstrip("%")])
        return rows

    def run(self):
        novo = not os.path.exists(RECURSOS)
        with open(RECURSOS, "a", encoding="utf-8") as f:
            if novo:
                f.write(",".join(self.COLS) + "\n")
        while not self.parar.wait(60):
            try:
                rows = self.amostra()
                with open(RECURSOS, "a", encoding="utf-8") as f:
                    for r in rows:
                        f.write(",".join(str(x) for x in r) + "\n")
            except Exception as e:  # o monitor nunca derruba a campanha
                log(f"monitor de recursos: {e}")


# ----------------------------------------------------------------- orquestração
def main():
    cfg = load_config()
    tools = cfg["TOOLS"].split()
    apis = cfg["APIS"].split()
    reps = int(cfg["REPS"])
    budget_min = int(cfg["BUDGET_MIN"])
    base_seed = int(cfg.get("BASE_SEED", "1000"))
    slots = int(cfg.get("SLOTS", "2"))
    lim = limites(slots)

    os.makedirs(ESTADO, exist_ok=True)
    if not os.path.exists(REGISTRO) or "## Registro automático da campanha" not in open(REGISTRO, encoding="utf-8").read():
        with open(REGISTRO, "a", encoding="utf-8") as f:
            f.write(REG_HEADER)

    if os.path.exists(PAUSAR):
        log("O arquivo PAUSAR existe: nenhuma execução foi iniciada. Apague-o (rm PAUSAR) para retomar.")
        return 0

    log(f"TOOLS=[{' '.join(tools)}] APIS=[{' '.join(apis)}] REPS={reps} BUDGET_MIN={budget_min} SLOTS={slots}")
    log("limites por contêiner: " + " ".join(f"{k}={v}" for k, v in lim.items()))

    limpar_restos()
    # execuções interrompidas numa sessão anterior
    for d in sorted(os.listdir(RAW)):
        p = os.path.join(RAW, d)
        if os.path.isdir(p) and "__rep" in d and not d.startswith("_") and not os.path.exists(os.path.join(p, "meta.json")):
            mover_incompleta(d, "estava incompleta (sem meta.json) ao iniciar o run_parallel")

    fila_total = montar_fila(tools, apis, reps, base_seed)
    pendentes = [it for it in fila_total if not concluida(it)]
    feitas = len(fila_total) - len(pendentes)
    registrar("início/retomada da campanha",
              f"{feitas} de {len(fila_total)} execuções já concluídas; {len(pendentes)} pendentes; "
              f"{slots} slots; orçamento {budget_min} min")
    log(f"{feitas} de {len(fila_total)} já concluídas; {len(pendentes)} na fila")
    if pendentes:
        est = len(pendentes) * (budget_min + 3) / slots / 60
        log(f"estimativa (sem contar a folga de minimização do EvoMaster): ~{est:.1f} h")

    em_andamento = {}            # slot -> run_id
    procs = {}                   # slot -> (Popen, item, t0)
    tentativas = {}
    monitor = Monitor(em_andamento)
    monitor.start()
    aviso_pausa = False

    def encerrar(signum, _frame):
        log(f"sinal {signum} recebido: interrompendo as execuções em andamento (ficarão incompletas e serão refeitas)")
        for p, _, _ in procs.values():
            try:   # o grupo inteiro: run_one.sh e o wrapper da ferramenta (o trap do run_one limpa os contêineres)
                os.killpg(p.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        for p, _, _ in procs.values():
            try:
                p.wait(60)
            except subprocess.TimeoutExpired:
                p.kill()
        registrar("interrupção", f"sinal {signum}; em andamento: {', '.join(em_andamento.values()) or 'nenhuma'}")
        sys.exit(1)

    signal.signal(signal.SIGTERM, encerrar)
    signal.signal(signal.SIGINT, encerrar)
    signal.signal(signal.SIGHUP, encerrar)

    def bombear(slot, proc):
        for line in proc.stdout:
            with _print_lock:
                print(f"[s{slot}] {line}", end="", flush=True)

    def iniciar(slot, item):
        api, tool, rep = item
        rid = run_id(item)
        viz = [r for s, r in em_andamento.items() if s != slot]
        gravar_json(os.path.join(ESTADO, rid + ".vizinhos"), viz)
        for s, r in em_andamento.items():
            vf = os.path.join(ESTADO, r + ".vizinhos")
            atual = json.load(open(vf)) if os.path.exists(vf) else []
            if rid not in atual:
                gravar_json(vf, atual + [rid])
        env = dict(os.environ)
        env.update(lim)
        env.update(API=api, TOOL=tool, REP=str(rep), SLOT=str(slot),
                   BUDGET_SEC=str(budget_min * 60), SEED=str(base_seed + rep), SLOTS=str(slots),
                   ESTADO_DIR=ESTADO, REGISTRO_DESVIOS=REGISTRO)
        for k in ("TOOLS", "APIS", "REPS", "BUDGET_MIN", "BASE_SEED", "ST_VERSION", "RESTLER_IMAGE", "EM_VERSION"):
            env[k] = cfg.get(k, "")
        p = subprocess.Popen(["bash", "scripts/run_one.sh"], env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, start_new_session=True)
        threading.Thread(target=bombear, args=(slot, p), daemon=True).start()
        procs[slot] = (p, item, time.time())
        em_andamento[slot] = rid
        gravar_json(os.path.join(ESTADO, "em_andamento.json"), {str(k): v for k, v in em_andamento.items()})
        log(f"slot {slot}: iniciando {rid} (vizinhos agora: {', '.join(viz) or 'nenhum'})")

    while True:
        # 1) execuções que terminaram
        for slot in list(procs):
            p, item, t0 = procs[slot]
            if p.poll() is None:
                continue
            rid = run_id(item)
            del procs[slot]; em_andamento.pop(slot, None)
            gravar_json(os.path.join(ESTADO, "em_andamento.json"), {str(k): v for k, v in em_andamento.items()})
            dur = (time.time() - t0) / 60
            if concluida(item):
                log(f"slot {slot}: {rid} concluída em {dur:.1f} min")
            else:
                tentativas[rid] = tentativas.get(rid, 0) + 1
                mover_incompleta(rid, f"falhou (código {p.returncode}, {dur:.1f} min, tentativa {tentativas[rid]})")
                if tentativas[rid] < MAX_TENTATIVAS:
                    pendentes.append(item)
                else:
                    log(f"!! {rid} falhou {MAX_TENTATIVAS} vezes; fica para a próxima sessão")
                    registrar("falha", f"`{rid}` falhou {MAX_TENTATIVAS} vezes nesta sessão; não foi refeita")

        # 2) pausa segura
        if os.path.exists(PAUSAR):
            if not procs:
                registrar("pausa", f"arquivo PAUSAR; {len(pendentes)} execuções pendentes; nenhuma em andamento")
                log("PAUSADO COM SEGURANÇA – pode desligar")
                monitor.parar.set()
                return 0
            if not aviso_pausa:
                log(f"PAUSAR detectado: nenhuma execução nova; aguardando {len(procs)} em andamento: "
                    + ", ".join(em_andamento.values()))
                aviso_pausa = True
        else:
            if aviso_pausa:
                log("PAUSAR removido antes do fim: a campanha continua")
            aviso_pausa = False
            # 3) slots livres
            for slot in range(slots):
                if slot in procs or not pendentes:
                    continue
                rodando = {it[1] for _, it, _ in procs.values()}
                escolha = next((it for it in pendentes if it[1] not in rodando), pendentes[0])
                pendentes.remove(escolha)
                if concluida(escolha):
                    continue
                iniciar(slot, escolha)

        # 4) fim
        if not procs and not pendentes:
            faltam = [run_id(it) for it in fila_total if not concluida(it)]
            if faltam:
                registrar("fim da sessão com falhas", "não concluídas: " + ", ".join(f"`{r}`" for r in faltam))
                log("sessão terminada; NÃO concluídas: " + ", ".join(faltam) + " (rode de novo para refazer)")
            else:
                registrar("campanha concluída", f"{len(fila_total)} de {len(fila_total)} execuções com meta.json")
                log(f"CAMPANHA CONCLUÍDA: {len(fila_total)} execuções. Próximo passo: python3 analysis/extract_findings.py")
            monitor.parar.set()
            return 0 if not faltam else 2
        time.sleep(POLL)


if __name__ == "__main__":
    sys.exit(main())
