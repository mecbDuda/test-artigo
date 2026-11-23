#!/usr/bin/env python3
"""Gera o corpo de docs/guia_classificacao.md (piloto) a partir de data/validated/relatos.csv e data/raw/.
Só lê dados; não altera relatos.csv. Uso: python3 analysis/gerar_guia_classificacao.py <raiz> data/validated/sugestoes_ia.csv"""
import csv, glob, json, os, re, shlex, sys, importlib.util

ROOT = sys.argv[1]
SUG = {r["chave"]: r for r in csv.DictReader(open(sys.argv[2], encoding="utf-8"))}
spec = importlib.util.spec_from_file_location("ef", os.path.join(ROOT, "analysis", "extract_findings.py"))
ef = importlib.util.module_from_spec(spec); spec.loader.exec_module(ef)
matcher = ef.OpMatcher(ef.load_spec(os.path.join(ROOT, "apis/vampi/openapi3.yml")))
BODY_DIR = os.path.join(ROOT, "docs", "guia_classificacao_corpos")
BASE = "http://localhost:8080"
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run_dir(tool):
    return os.path.join(ROOT, "data", "raw", f"vampi__{tool}__rep1")


def load_api_log(tool):
    with open(os.path.join(run_dir(tool), "api.log"), encoding="utf-8", errors="replace") as f:
        return [ANSI.sub("", l.rstrip("\n")).replace("api-1  | ", "", 1) for l in f]


LOGS = {t: load_api_log(t) for t in ("schemathesis", "restler", "evomaster")}
FLOWS = {t: ef.read_flows(run_dir(t)) for t in LOGS}


def body_arg(chave, body):
    if not body:
        return ""
    if len(body) > 400:
        os.makedirs(BODY_DIR, exist_ok=True)
        p = os.path.join(BODY_DIR, f"{chave}.json")
        open(p, "w", encoding="utf-8").write(body)
        return f" -H 'Content-Type: application/json' --data-binary @docs/guia_classificacao_corpos/{chave}.json"
    return f" -H 'Content-Type: application/json' -d {shlex.quote(body)}"


def make_curl(chave, method, path, query="", body="", auth=False):
    url = BASE + path + (f"?{query}" if query else "")
    a = ' -H "Authorization: Bearer $TOKEN"' if auth else ""
    return f"curl -i --path-as-is -X {method}{a}{body_arg(chave, body)} {shlex.quote(url)}"


ACCESS = re.compile(r'^\d+\.\d+\.\d+\.\d+ - - \[')


def path_variants(path):
    import urllib.parse
    dec = urllib.parse.unquote(path, errors="replace")
    reenc = "".join(f"%{ord(c):02X}" if ord(c) < 0x20 else c for c in dec)
    return list(dict.fromkeys([path, reenc, dec]))


def log_excerpt(tool, method, path, status):
    """Linha de acesso do api.log com método, caminho e status esperados; para 500,
    acrescenta o traceback que o Werkzeug grava logo depois dela."""
    if status is None:
        return None, None
    lines = LOGS[tool]
    pats = [f'"{method} {p} HTTP/1.1" {status} ' for p in path_variants(path)]
    for i, l in enumerate(lines):
        if any(pt in l for pt in pats):
            if str(status) != "500":
                return l, i + 1
            k = i + 1
            while k < len(lines) and not ACCESS.match(lines[k]):
                k += 1
            tb = lines[i + 1:k]
            keep = []
            for n, x in enumerate(tb):
                if "/vampi/" in x or "api_views" in x:
                    keep += [x] + tb[n + 1:n + 2]
            exc = [x for x in tb if re.match(r"^[\w.]+(Error|Exception)\b", x)]
            body = [l] + (["Traceback (trecho):"] + keep[-4:] + ["..."] + exc[-1:] if tb else [])
            return "\n".join(body), i + 1
    return None, None


def first_flow(tool, op, pred):
    for r in FLOWS[tool]:
        if matcher.match(r["method"], r["path"]) == op and pred(r):
            return r
    return None


def from_5xx(rel, tool):
    def pred(r):
        if r["status"] < 500:
            return False
        sig = f"{r['status']} " + ef.norm_sig(ef.body_sig(r.get("resp_body")))
        return sig == rel["assinatura"]
    r = first_flow(tool, rel["operacao"], pred)
    if not r:
        return None
    auth = any(k.lower() == "authorization" for k in r.get("req_headers", {}))
    return r["method"], r["path"], r.get("query", ""), r.get("req_body", ""), auth, r["status"]


def from_schemathesis(rel):
    code = rel["tipo"].split(":")[1]
    for xml in glob.glob(os.path.join(run_dir("schemathesis"), "iter_*", "*.xml")):
        txt = open(xml, encoding="utf-8").read()
        import xml.etree.ElementTree as ET
        for tc in ET.parse(xml).iter("testcase"):
            name = tc.get("name", "")
            if rel["operacao"] != "Stateful tests" and not name.endswith(rel["operacao"]):
                continue
            if rel["operacao"] == "Stateful tests" and "Stateful" not in name:
                continue
            for ch in tc:
                t = ch.text or ""
                # cada caso: bloco que contém "- STxxx" seguido do curl
                for blk in re.split(r"\n(?=\d+\. Test Case ID)", t):
                    if re.search(rf"^\s*-\s+{code}\b", blk, re.M):
                        curls = re.findall(r"^\s*(curl .+)$", blk, re.M)
                        st = re.search(r"^\[(\d{3})\]", blk, re.M)
                        if curls:
                            return curls, (st.group(1) if st else None)
    return None


def parse_st_curl(c):
    """Extrai método, caminho, corpo e se havia Authorization de um curl do Schemathesis."""
    toks = shlex.split(c)
    m, body, auth, url = "GET", "", False, ""
    i = 1
    while i < len(toks):
        t = toks[i]
        if t == "-X": m = toks[i + 1]; i += 2; continue
        if t == "-H":
            if toks[i + 1].lower().startswith("authorization"): auth = True
            i += 2; continue
        if t == "-d": body = toks[i + 1]; i += 2; continue
        url = t; i += 1
    path = re.sub(r"^https?://[^/]+", "", url)
    p, _, q = path.partition("?")
    return m, p, q, body, auth


def from_restler(rel):
    b = rel["exemplo"]
    p = glob.glob(os.path.join(run_dir("restler"), "**", "bug_buckets", b), recursive=True)[0]
    txt = open(p, encoding="utf-8").read()
    reqs = re.findall(r"^-> (\w+) (\S+) HTTP/1.1(.*)$", txt, re.M)
    out = []
    for m, path, rest in reqs:
        parts = rest.split("\\r\\n\\r\\n", 1)
        body = parts[1].rsplit("\\r\\n", 1)[0] if len(parts) > 1 else ""
        body = body.encode().decode("unicode_escape") if body else ""
        p0, _, q = path.partition("?")
        out.append((m, p0, q, body, "AUTHORIZATION TOKEN" in rest))
    return out, os.path.relpath(p, ROOT)


def from_evomaster(rel):
    test = rel["exemplo"].split("#")[1].split(" |")[0]
    src = open(os.path.join(run_dir("evomaster"), "generated_tests", "EvoMaster_faults_Test.java"), encoding="utf-8").read()
    m = re.search(rf"void {test}\(\).*?\n    \}}", src, re.S)
    blk = m.group(0)
    call = re.search(r"\.(get|post|put|delete|patch)\(baseUrlOfSut \+ \"([^\"]*)\"", blk)
    body = re.search(r'\.body\((.*?)\)\s*\n\s*\.(get|post|put|delete|patch)\(', blk, re.S)
    auth = "Authorization" in blk
    b = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', body.group(1))).encode().decode("unicode_escape").strip() if body else ""
    st = re.search(r"\.statusCode\((\d{3})\)", blk)
    p, _, q = call.group(2).partition("?")
    return call.group(1).upper(), p, q, b, auth, (st.group(1) if st else None)


def main():
    rels = list(csv.DictReader(open(os.path.join(ROOT, "data/validated/relatos.csv"), encoding="utf-8")))
    out = []
    for n, r in enumerate(rels, 1):
        tools = r["ferramentas"].split(";")
        tool = tools[0]
        curls, excerpt, line, fonte, extra = [], None, None, "", ""
        if r["tipo"] == "http_5xx":
            for t in tools:
                x = from_5xx(r, t)
                if x:
                    tool = t; m, p, q, b, a, st = x
                    curls.append(make_curl(r["chave"], m, p, q, b, a))
                    excerpt, line = log_excerpt(t, m, p, st)
                    fonte = f"primeira resposta 5xx com esta assinatura em `data/raw/vampi__{t}__rep1/flows.jsonl`"
                    break
        elif r["tipo"].startswith("schemathesis:"):
            cs, st = from_schemathesis(r) or ([], None)
            fonte = "curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)"
            for c in cs:
                m, p, q, b, a = parse_st_curl(c)
                curls.append(make_curl(r["chave"], m, p, q, b, a))
            if cs:
                m, p, q, b, a = parse_st_curl(cs[-1])
                excerpt, line = log_excerpt("schemathesis", m, p, st)
            if "[Filtered]" in " ".join(curls):
                extra = "O Schemathesis mascara segredos como `[Filtered]` no relatório; troque pelo valor usado (ex.: senha) ou por um valor qualquer."
        elif r["tipo"].startswith("restler:"):
            reqs, path = from_restler(r)
            fonte = f"sequência do *bug bucket* do RESTler (`{path}`)"
            for m, p, q, b, a in reqs:
                curls.append(make_curl(r["chave"], m, p, q, b, a))
            m, p = reqs[-1][0], reqs[-1][1]
            st = re.search(r"_(\d{3})_", r["exemplo"])
            excerpt, line = log_excerpt("restler", m, p, st.group(1) if st else None)
        elif r["tipo"].startswith("evomaster:"):
            m, p, q, b, a, st = from_evomaster(r)
            fonte = f"teste `{r['exemplo'].split(' |')[0]}` em `generated_tests/EvoMaster_faults_Test.java`"
            curls.append(make_curl(r["chave"], m, p, q, b, a))
            excerpt, line = log_excerpt("evomaster", m, p, st)
        s = SUG.get(r["chave"], {})
        out.append(f"### {n}. `{r['chave']}` — {r['operacao']} · `{r['tipo']}`\n")
        out.append(f"- **Operação afetada:** `{r['operacao']}`")
        out.append(f"- **Ferramenta(s):** {r['ferramentas']}")
        out.append(f"- **Assinatura:** `{r['assinatura']}`")
        out.append(f"- **Origem da requisição:** {fonte}")
        out.append(f"- **sugestao_ia:** **{s.get('sugestao_ia','')}** — {s.get('justificativa','')}\n")
        out.append("```bash\n" + ("\n".join(curls) if curls else "# requisição não localizada automaticamente; ver coluna exemplo") + "\n```")
        if extra:
            out.append(extra + "\n")
        if excerpt:
            out.append(f"Trecho de `data/raw/vampi__{tool}__rep1/api.log` (linha {line}):\n")
            out.append("```text\n" + excerpt + "\n```\n")
        else:
            out.append(f"Trecho do `api.log`: nenhuma linha de acesso com método, caminho e status esperados em `vampi__{tool}__rep1/api.log` (ex.: requisição que terminou em *timeout*, sem status registrado).\n")
    return "\n".join(out), len(rels)


if __name__ == "__main__":
    body, n = main()
    sys.stdout.write(body)
