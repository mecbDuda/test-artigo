#!/usr/bin/env python3
"""
Reproduz, com a API em ESTADO LIMPO, a requisição de evidência de cada relato de
data/validated/relatos.csv e grava o resultado para apoiar a revisão da equipe.

Evidência usada por tipo de relato (sempre de data/raw/, nunca alterada):
  http_5xx               primeira requisição com resposta 5xx de mesma assinatura em flows.jsonl
  schemathesis:STxxx     comando curl "Reproduce with" do relatório JUnit
                         (cabeçalho Authorization e campos "[Filtered]" são substituídos
                         por um token novo e por um valor fixo)
  restler:<Checker>      sequência de requisições do bug bucket (.txt) do RESTler
  evomaster:<código>     chamadas HTTP do teste gerado citado em report.json (testCaseId)

Estado limpo: antes de cada relato a API é reiniciada (petclinic-rest, catwatch: H2 em
memória) ou recriada com GET /createdb (VAmPI), num projeto compose próprio
("val_<api>", porta 8180+i), com os mesmos limites de CPU/memória da campanha.
Para erros que dependem de estado (ex.: UNIQUE constraint), se a 1ª tentativa não
reproduz, a sequência é repetida uma vez sem reiniciar (2ª tentativa).

Saídas (derivadas; podem ser apagadas e geradas de novo):
  data/processed/reproducao.csv              uma linha por relato
  data/processed/reproducao/<chave>.txt      requisições, respostas e trecho do log da API

Uso: python3 analysis/reproduzir.py [--apis vampi ...] [--chaves k1,k2]
"""
import argparse
import csv
import glob
import importlib.util
import json
import os
import re
import shlex
import socket
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT_DIR = os.path.join(ROOT, "data", "processed", "reproducao")
OUT_CSV = os.path.join(ROOT, "data", "processed", "reproducao.csv")
TIMEOUT = 30          # s por requisição (um timeout também é registrado: ReDoS, por exemplo)
FILTERED = "valorFiltrado1"

_spec = importlib.util.spec_from_file_location("ef", os.path.join(ROOT, "analysis", "extract_findings.py"))
ef = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ef)


# ------------------------------------------------------------------ cliente HTTP cru
def http(port, method, target, headers=None, body=b""):
    """Envia a requisição exatamente como recebida (sem normalizar a URL). Devolve
    (status, headers_dict, corpo_texto, ms) ou (None, {}, erro, ms)."""
    if isinstance(body, str):
        body = body.encode("utf-8", "surrogateescape")
    hdrs = {k: v for k, v in (headers or {}).items() if k.lower() not in ("host", "content-length", "connection")}
    lines = [f"{method} {target} HTTP/1.1", f"Host: localhost:{port}", "Connection: close"]
    lines += [f"{k}: {v}" for k, v in hdrs.items()]
    if body or method in ("POST", "PUT", "PATCH"):
        lines.append(f"Content-Length: {len(body)}")
    raw = ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8", "surrogateescape") + body
    t0 = time.time()
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=TIMEOUT) as s:
            s.sendall(raw)
            chunks = []
            while True:
                b = s.recv(65536)
                if not b:
                    break
                chunks.append(b)
    except (socket.timeout, TimeoutError):
        return None, {}, f"TIMEOUT ({TIMEOUT} s)", round((time.time() - t0) * 1000)
    except OSError as e:
        return None, {}, f"ERRO DE CONEXÃO: {e}", round((time.time() - t0) * 1000)
    ms = round((time.time() - t0) * 1000)
    data = b"".join(chunks)
    head, _, rest = data.partition(b"\r\n\r\n")
    hl = head.decode("latin-1").split("\r\n")
    m = re.match(r"HTTP/\d\.\d (\d{3})", hl[0] if hl else "")
    if not m:
        return None, {}, f"RESPOSTA INVÁLIDA: {data[:200]!r}", ms
    h = {}
    for l in hl[1:]:
        k, _, v = l.partition(":")
        h[k.strip().lower()] = v.strip()
    if "chunked" in h.get("transfer-encoding", ""):
        out, buf = b"", rest
        while buf:
            size_s, _, buf = buf.partition(b"\r\n")
            try:
                n = int(size_s.split(b";")[0], 16)
            except ValueError:
                break
            if n == 0:
                break
            out += buf[:n]; buf = buf[n + 2:]
        rest = out
    return int(m.group(1)), h, rest.decode("utf-8", "replace"), ms


# ------------------------------------------------------------------ API de validação
class ApiLimpa:
    def __init__(self, api, idx):
        self.api, self.port = api, 8180 + idx
        self.proj = f"val_{api.replace('-', '')}"
        self.env = dict(os.environ, PROXY_PORT=str(self.port), LOG_DIR=f"/tmp/{self.proj}")
        lim = subprocess.run(["bash", os.path.join(ROOT, "scripts", "limites.sh"), "2"], capture_output=True, text=True).stdout
        self.env.update(dict(l.split("=", 1) for l in lim.split()))
        os.makedirs(self.env["LOG_DIR"], exist_ok=True)
        self.cfg = self._api_env()
        self.compose = ["docker", "compose", "-p", self.proj, "-f", os.path.join(ROOT, "apis", api, "docker-compose.yml")]

    def _api_env(self):
        out = subprocess.run(["bash", "-c", f"set -a; source apis/{self.api}/api.env; env -0"], cwd=ROOT,
                             env=self.env, capture_output=True).stdout.decode()
        return dict(kv.split("=", 1) for kv in out.split("\0") if "=" in kv)

    def base_path(self):
        return re.sub(r"^https?://[^/]+", "", self.cfg["BASE_URL"]).rstrip("/")

    def _sh(self, *args):
        return subprocess.run(self.compose + list(args), env=self.env, cwd=ROOT, capture_output=True, text=True)

    def subir(self):
        self._sh("down", "-v", "--remove-orphans")
        self._sh("up", "-d")
        self._esperar()

    def _esperar(self):
        url = self.cfg["HEALTH_URL"]
        target = re.sub(r"^https?://[^/]+", "", url) or "/"
        for _ in range(120):
            st, _, _, _ = http(self.port, "GET", target)
            if st and st < 500:
                return
            time.sleep(1)
        raise RuntimeError(f"{self.api}: API de validação não respondeu")

    sujo = False   # True depois de uma reprodução que pode ter mudado o estado (não só GET)

    def resetar(self):
        """Estado limpo. Devolve o instante (para recortar o log da API). Se a reprodução
        anterior só fez GET/HEAD/OPTIONS, o estado continua limpo e a API não é reiniciada."""
        if not self.sujo:
            self.marca = time.time()
            if self.api == "vampi":
                http(self.port, "GET", "/createdb")
            return self.marca
        self.sujo = False
        if self.api == "vampi":
            self.marca = time.time()
            http(self.port, "GET", "/createdb")
        else:
            self._sh("restart", "api")
            self.marca = time.time()
            self._esperar()
        return self.marca

    def token(self):
        if self.api != "vampi":
            return None
        st, _, body, _ = http(self.port, "POST", "/users/v1/login", {"Content-Type": "application/json"},
                              '{"username":"name1","password":"pass1"}')
        try:
            return "Bearer " + json.loads(body)["auth_token"]
        except Exception:
            return None

    def log_desde(self, t):
        since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t - 1))   # UTC explícito
        out = self._sh("logs", "--no-color", "--since", since, "api").stdout
        return "\n".join(out.splitlines()[-150:])

    def descer(self):
        self._sh("down", "-v", "--remove-orphans")


# ------------------------------------------------------------------ evidências
def runs_da_chave():
    m = defaultdict(list)
    with open(os.path.join(ROOT, "data", "processed", "achados_por_execucao.csv"), encoding="utf-8") as f:
        for a in csv.DictReader(f):
            m[a["chave"]].append(a["run_id"])
    return m


def _target(path, query=""):
    return path + (("?" + query) if query else "")


def ev_5xx(rel, runs, spec_cache):
    for run in runs:
        d = os.path.join(RAW, run)
        meta = json.load(open(os.path.join(d, "meta.json")))
        matcher = spec_cache(meta["schema_file"])
        for r in ef.read_flows(d):
            if r["status"] < 500 or matcher.match(r["method"], r["path"]) != rel["operacao"]:
                continue
            sig = f"{r['status']} " + ef.norm_sig(ef.body_sig(r.get("resp_body")))
            if sig != rel["assinatura"]:
                continue
            h = {}
            for k, v in (r.get("req_headers") or {}).items():
                h[k] = v
            nota = "corpo da requisição truncado em 4000 caracteres no flows.jsonl" if len(r.get("req_body") or "") >= 4000 else ""
            return {"fonte": f"{run}/flows.jsonl (ts {r['ts']:.0f})", "nota": nota, "status_original": r["status"],
                    "passos": [{"method": r["method"], "target": _target(r["path"], r.get("query", "")), "headers": h,
                                "body": r.get("req_body") or ""}]}
    return None


def parse_curl(cmd):
    try:
        toks = shlex.split(cmd)
    except ValueError:
        return None
    method, headers, body, url = "GET", {}, "", None
    i = 1
    while i < len(toks):
        t = toks[i]
        if t in ("-X", "--request"):
            method = toks[i + 1]; i += 2; continue
        if t in ("-H", "--header"):
            hv = toks[i + 1]
            if ":" not in hv and hv.endswith(";"):      # sintaxe do curl: "Nome;" = cabeçalho vazio
                headers[hv[:-1].strip()] = ""; i += 2; continue
            k, _, v = hv.partition(":"); headers[k.strip()] = v.strip(); i += 2; continue
        if t in ("-d", "--data", "--data-raw", "--data-binary"):
            body = toks[i + 1]; i += 2
            if method == "GET":
                method = "POST"
            continue
        if not t.startswith("-"):
            url = t
        i += 1
    if not url:
        return None
    target = re.sub(r"^https?://[^/]+", "", url) or "/"
    return {"method": method, "target": target, "headers": headers, "body": body}


def ev_schemathesis(rel, runs, _):
    code = rel["tipo"].split(":")[1]
    for run in runs:
        for xml in sorted(glob.glob(os.path.join(RAW, run, "iter_*", "**", "*.xml"), recursive=True)):
            try:
                tree = ET.parse(xml)
            except ET.ParseError:
                continue
            for tc in tree.iter("testcase"):
                name = tc.get("name", "")
                m = re.search(r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(\S+)", name)
                op = f"{m.group(1)} {m.group(2)}" if m else name
                if op != rel["operacao"]:
                    continue
                for ch in tc:
                    if ch.tag not in ("failure", "error"):
                        continue
                    for bloco in re.split(r"\n\s*\d+\. Test Case ID", ch.text or ""):
                        if not re.search(rf"^\s*-\s+{code}\b", bloco, re.M):
                            continue
                        curls = re.findall(r"^\s*(curl .+)$", bloco, re.M)
                        st = re.search(r"^\[(\d{3})\]", bloco, re.M)
                        passos = [p for p in (parse_curl(c) for c in curls) if p]
                        if passos:
                            return {"fonte": f"{run}/{os.path.relpath(xml, os.path.join(RAW, run))}", "nota": "",
                                    "status_original": int(st.group(1)) if st else "", "passos": passos,
                                    "trecho": bloco.strip()[:1500]}
    return None


def ev_restler(rel, runs, _):
    alvo = rel["exemplo"]
    for run in runs:
        for p in glob.glob(os.path.join(RAW, run, "**", "bug_buckets", alvo), recursive=True):
            txt = open(p, encoding="utf-8", errors="replace").read()
            passos = []
            for line in txt.splitlines():
                if not line.startswith("-> "):
                    continue
                lit = line[3:].strip()
                if len(lit) >= 2 and lit[0] == lit[-1] and lit[0] in "'\"":   # repr com aspas
                    lit = lit[1:-1]
                raw = lit.encode("latin-1", "backslashreplace").decode("unicode_escape", "replace")
                head, _, body = raw.partition("\r\n\r\n")
                hl = head.split("\r\n")
                m = re.match(r"(\S+) (\S+) HTTP/1\.1", hl[0])
                if not m:
                    continue
                h = {}
                for l in hl[1:]:
                    if l.strip() == "AUTHORIZATION TOKEN":   # marcador do RESTler: token vai aqui
                        h["Authorization"] = ""
                        continue
                    k, _, v = l.partition(":")
                    if k:
                        h[k.strip()] = v.strip()
                passos.append({"method": m.group(1), "target": m.group(2), "headers": h, "body": body.rstrip("\r\n")})
            st = re.findall(r"PREVIOUS RESPONSE: 'HTTP/1\.1 (\d{3})", txt)
            if passos:
                return {"fonte": f"{run}/{os.path.relpath(p, os.path.join(RAW, run))}", "nota": "",
                        "status_original": int(st[-1]) if st else "", "passos": passos}
    return None


def _java_str(expr):
    """Concatena os literais Java de uma expressão como "a" + "b"."""
    return "".join(json.loads('"' + s + '"') for s in re.findall(r'"((?:[^"\\]|\\.)*)"', expr))


def ev_evomaster(rel, runs, spec_cache):
    for run in runs:
        rep = os.path.join(RAW, run, "generated_tests", "report.json")
        if not os.path.exists(rep):
            continue
        matcher = spec_cache(json.load(open(os.path.join(RAW, run, "meta.json")))["schema_file"])
        data = json.load(open(rep))
        for fault in (data.get("faults") or {}).get("foundFaults") or []:
            m = re.match(r"([A-Za-z]+):(.*)", fault.get("operationId", ""))
            if not m:
                continue
            op = f"{m.group(1).upper()} {m.group(2)}"
            if op not in matcher.ops:          # mesma regra do extract_findings.py
                op = matcher.match(m.group(1), m.group(2))
            if op != rel["operacao"]:
                continue
            ctx = [ef.norm_sig(c.get("context", "")) for c in fault.get("faultCategories") or []]
            if rel["assinatura"] not in ctx:
                continue
            arq, _, metodo = fault.get("testCaseId", "").partition("#")
            jp = os.path.join(RAW, run, "generated_tests", arq)
            if not os.path.exists(jp):
                continue
            src = open(jp, encoding="utf-8", errors="replace").read()
            mm = re.search(rf"void {re.escape(metodo)}\(\)[^{{]*\{{(.*?)\n    \}}\n", src, re.S)
            if not mm:
                continue
            corpo = mm.group(1)
            passos, status = [], ""
            for chamada in re.split(r"\bgiven\(\)", corpo)[1:]:
                mc = re.search(r"\.(get|post|put|patch|delete|head|options)\((.*?)\)\s*\n\s*\.then\(\)", chamada, re.S)
                if not mc:
                    continue
                url_expr = mc.group(2)
                resto = re.sub(r'"(?:[^"\\]|\\.)*"', "", url_expr).replace("baseUrlOfSut", "")
                if re.search(r"[A-Za-z_]", resto):
                    return {"fonte": f"{run}/generated_tests/{arq}#{metodo}", "nota": "URL depende de variável do teste (ex.: Location de uma chamada anterior); reprodução manual",
                            "status_original": "", "passos": [], "trecho": corpo[:1500]}
                req = chamada[:mc.start() + 1]     # só a parte da requisição (antes de .then(): asserções)
                h = {}
                for k, v in re.findall(r'\.header\("([^"]+)",\s*"((?:[^"\\]|\\.)*)"\)', req):
                    h[k] = json.loads('"' + v + '"')
                ct = re.search(r'\.contentType\("([^"]+)"\)', req)
                if ct:
                    h["Content-Type"] = ct.group(1)
                acc = re.match(r'\.accept\("([^"]+)"\)', req.strip())
                if acc:
                    h["Accept"] = acc.group(1)
                mb = re.search(r"\.body\((.*)\)\s*\n\s*\.$", req, re.S)
                body = _java_str(mb.group(1)) if mb else ""
                passos.append({"method": mc.group(1).upper(), "target": _java_str(url_expr) or "/", "headers": h, "body": body})
                s = re.search(r"\.statusCode\((\d{3})\)", chamada)
                status = int(s.group(1)) if s else ""
            if passos:
                return {"fonte": f"{run}/generated_tests/{arq}#{metodo}", "nota": "", "status_original": status,
                        "passos": passos, "trecho": corpo[:1500]}
    return None


EVIDENCIA = {"http_5xx": ev_5xx, "schemathesis": ev_schemathesis, "restler": ev_restler, "evomaster": ev_evomaster}


# ------------------------------------------------------------------ reprodução
def ajustar(passo, api, token, base):
    p = dict(passo, headers=dict(passo["headers"]))
    for k in list(p["headers"]):
        if k.lower() == "authorization":
            if token:
                p["headers"][k] = token
            else:
                del p["headers"][k]
    body = p["body"] or ""
    p["body"] = body.replace("[Filtered]", FILTERED)
    return p


def reproduzir(rel, ev, api_limpa):
    linhas, final, tentativa = [], None, 0
    t0 = api_limpa.resetar()
    for tentativa in (1, 2):
        token = api_limpa.token()
        for i, passo in enumerate(ev["passos"]):
            p = ajustar(passo, rel["api"], token, api_limpa.base_path())
            st, h, body, ms = http(api_limpa.port, p["method"], p["target"], p["headers"], p["body"])
            if p["method"].upper() not in ("GET", "HEAD", "OPTIONS"):
                api_limpa.sujo = True
            final = (st, h, body, ms)
            linhas.append(f"[tentativa {tentativa}, passo {i + 1}] {p['method']} {p['target']}\n"
                          f"  cabeçalhos: {json.dumps(p['headers'], ensure_ascii=False)}\n"
                          f"  corpo: {p['body'][:1500]}\n"
                          f"  -> {st} ({ms} ms) content-type={h.get('content-type', '')}\n"
                          f"  resposta: {body[:1500]}\n")
        if ok(rel, ev, final):
            break
    log = api_limpa.log_desde(t0)
    return final, tentativa, "\n".join(linhas), log


def ok(rel, ev, final):
    st, h, body, _ = final
    if rel["tipo"] == "http_5xx":
        return st is not None and st >= 500 and f"{st} " + ef.norm_sig(ef.body_sig(body)) == rel["assinatura"]
    if st is None:
        return False
    so = ev.get("status_original")
    return so != "" and st == so


def processar_api(api, idx, itens, ate):
    out = []
    v = ApiLimpa(api, idx)
    v.subir()
    try:
        for rel, ev in itens:
            if ev is None or not ev["passos"]:
                out.append(linha(rel, ev, None, 0, "não", (ev or {}).get("nota") or "evidência sem requisição reproduzível"))
                escrever_txt(rel, ev, "", "")
                continue
            final, tent, troca, log = reproduzir(rel, ev, v)
            r = "sim" if ok(rel, ev, final) else "não"
            out.append(linha(rel, ev, final, tent, r, ev.get("nota", "")))
            escrever_txt(rel, ev, troca, log)
            print(f"[{api}] {rel['chave']} {rel['tipo']:<32} -> {final[0]} reproduzido={r}", flush=True)
    finally:
        v.descer()
    return out


def linha(rel, ev, final, tent, rep, nota):
    st, h, body = (final or (None, {}, ""))[:3]
    return {"chave": rel["chave"], "api": rel["api"], "operacao": rel["operacao"], "tipo": rel["tipo"],
            "fonte_evidencia": (ev or {}).get("fonte", ""), "n_passos": len((ev or {}).get("passos", [])),
            "status_original": (ev or {}).get("status_original", ""),
            "status_reproduzido": "" if final is None else (st if st is not None else body[:40]),
            "content_type_reproduzido": h.get("content-type", ""),
            "assinatura_reproduzida": "" if not st else f"{st} " + ef.norm_sig(ef.body_sig(body)),
            "tentativas": tent, "reproduzido": rep, "nota": nota}


# tokens JWT (do VAmPI local, descartável) não são gravados nas evidências
JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")


def sem_token(texto):
    return JWT_RE.sub("<JWT removido>", texto)


def escrever_txt(rel, ev, troca, log):
    partes = [f"relato {rel['chave']} | {rel['api']} | {rel['operacao']} | {rel['tipo']}\n",
              f"assinatura: {rel['assinatura']}\nferramentas: {rel['ferramentas']}\n",
              f"evidência: {(ev or {}).get('fonte', '(não encontrada)')}\n{(ev or {}).get('nota', '')}\n\n"]
    if ev and ev.get("trecho"):
        partes.append("=== trecho do relatório da ferramenta ===\n" + ev["trecho"] + "\n\n")
    partes.append("=== reprodução em estado limpo ===\n" + (troca or "(não executada)\n"))
    partes.append("\n=== log da API durante a reprodução (últimas 150 linhas) ===\n" + (log or "") + "\n")
    with open(os.path.join(OUT_DIR, rel["chave"] + ".txt"), "w", encoding="utf-8") as f:
        f.write(sem_token("".join(partes)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apis", nargs="*")
    ap.add_argument("--chaves")
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    rels = list(csv.DictReader(open(os.path.join(ROOT, "data", "validated", "relatos.csv"), encoding="utf-8")))
    if args.apis:
        rels = [r for r in rels if r["api"] in args.apis]
    if args.chaves:
        ks = set(args.chaves.split(","))
        rels = [r for r in rels if r["chave"] in ks]
    rmap = runs_da_chave()
    cache = {}

    def spec_cache(path):
        if path not in cache:
            cache[path] = ef.OpMatcher(ef.load_spec(os.path.join(ROOT, path)))
        return cache[path]

    por_api = defaultdict(list)
    for r in rels:
        fam = r["tipo"].split(":")[0]
        fn = EVIDENCIA.get(fam)
        ev = fn(r, rmap.get(r["chave"], []), spec_cache) if fn else None
        por_api[r["api"]].append((r, ev))

    apis = sorted(por_api)
    with ThreadPoolExecutor(max_workers=len(apis) or 1) as ex:
        res = list(ex.map(lambda ia: processar_api(ia[1], ia[0], por_api[ia[1]], None), enumerate(apis)))
    rows = [x for part in res for x in part]

    # mescla com execuções anteriores (outras APIs/chaves)
    old = {}
    if os.path.exists(OUT_CSV):
        old = {r["chave"]: r for r in csv.DictReader(open(OUT_CSV, encoding="utf-8"))}
    old.update({r["chave"]: r for r in rows})
    fields = list(rows[0].keys()) if rows else list(next(iter(old.values())).keys())
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for k in sorted(old):
            w.writerow(old[k])
    n = sum(1 for r in rows if r["reproduzido"] == "sim")
    print(f"{len(rows)} relatos processados; {n} reproduzidos. Saída: {OUT_CSV}")


if __name__ == "__main__":
    sys.exit(main())
