#!/usr/bin/env python3
"""
Lê data/raw/<execução>/ e produz:

  data/processed/run_stats.csv            métricas de exploração por execução
  data/processed/achados_por_execucao.csv achados deduplicados dentro de cada execução
  data/validated/relatos.csv              lista ÚNICA de relatos a validar manualmente
                                          (preserva classificações já preenchidas)

Fontes de achados:
  * proxy (todas as ferramentas): respostas HTTP 5xx  -> tipo "http_5xx"
  * Schemathesis: relatórios JUnit (violações de contrato etc.)
  * RESTler: arquivos de bug_buckets (checkers)
  * EvoMaster: comentários de falha nos testes gerados (heurística)

Os parsers dos relatórios das ferramentas são heurísticos: na primeira execução de
teste, confira se os achados de cada ferramenta aparecem em achados_por_execucao.csv.

Uso: python3 analysis/extract_findings.py [--raw data/raw]
"""
import argparse
import csv
import glob
import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

try:
    import yaml
except ImportError:  # especificações em JSON continuam funcionando
    yaml = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METHODS = ("get", "post", "put", "patch", "delete", "head", "options")
CLASS_COLS = ["classificacao", "defeito_id", "avaliador_1", "avaliador_2", "observacoes"]


# ---------------------------------------------------------------- especificação
def load_spec(path):
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    if path.endswith(".json") or yaml is None:
        return json.loads(txt)
    return yaml.safe_load(txt)


class OpMatcher:
    """Converte caminhos concretos (/users/v1/ana) em operações (GET /users/v1/{username})."""

    def __init__(self, spec):
        base = ""
        servers = spec.get("servers") or []
        if servers:
            url = servers[0].get("url", "")
            base = re.sub(r"^https?://[^/]+", "", url).rstrip("/")
        elif spec.get("basePath"):
            base = spec["basePath"].rstrip("/")
        self.ops, self.rules = [], []
        for tpl, item in (spec.get("paths") or {}).items():
            for m in item:
                if m.lower() in METHODS:
                    self.ops.append(f"{m.upper()} {tpl}")
            rx = "^" + re.escape(base + tpl) + "/?$"
            rx = re.sub(r"\\\{[^}]+\\\}", r"[^/]+", rx)
            n_params = tpl.count("{")
            self.rules.append((n_params, re.compile(rx), tpl))
        self.rules.sort(key=lambda r: r[0])  # caminhos literais têm prioridade

    def match(self, method, path):
        for _, rx, tpl in self.rules:
            if rx.match(path):
                return f"{method.upper()} {tpl}"
        return f"{method.upper()} {path} (fora da especificação)"


# ---------------------------------------------------------------- utilitários
def norm_sig(text, limit=120):
    text = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    text = re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}", "<uuid>", text)
    text = re.sub(r"\d+", "<n>", text)
    text = re.sub(r"\s+", " ", text).lower()
    return text[:limit]


def key_of(api, op, kind, sig):
    return hashlib.sha1(f"{api}|{op}|{kind}|{sig}".encode()).hexdigest()[:12]


def read_flows(run_dir):
    p = os.path.join(run_dir, "flows.jsonl")
    if not os.path.exists(p):
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return sorted(out, key=lambda r: r["ts"])


# ---------------------------------------------------------------- parsers
def findings_schemathesis(run_dir, matcher):
    res = []
    for xml in glob.glob(os.path.join(run_dir, "iter_*", "**", "*.xml"), recursive=True):
        try:
            tree = ET.parse(xml)
        except ET.ParseError:
            continue
        for tc in tree.iter("testcase"):
            name = tc.get("name", "")
            m = re.search(r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(\S+)", name)
            op = f"{m.group(1)} {m.group(2)}" if m else name
            for child in list(tc):
                if child.tag not in ("failure", "error"):
                    continue
                msg = (child.get("message") or child.text or "").strip()
                for block in re.split(r"\n\s*\n", msg) or [msg]:
                    low = block.lower()
                    if "server error" in low or re.search(r"\b5\d\d\b", low) and "status" not in low:
                        kind = "http_5xx"          # já coberto pelo proxy; mantido para conferência
                    elif "schema" in low:
                        kind = "schema_violation"
                    elif "status code" in low or "undocumented" in low:
                        kind = "undocumented_status"
                    elif "content-type" in low or "content type" in low:
                        kind = "content_type"
                    elif "header" in low:
                        kind = "missing_header"
                    elif not block.strip():
                        continue
                    else:
                        kind = "other"
                    res.append({"op": op, "kind": f"schemathesis:{kind}", "sig": norm_sig(block), "example": block[:300]})
    return res


def findings_restler(run_dir, matcher):
    res = []
    for p in glob.glob(os.path.join(run_dir, "**", "bug_buckets", "*.txt"), recursive=True):
        base = os.path.basename(p)
        if base.startswith("bug_buckets"):
            continue
        checker = base.split("_")[0]
        status = re.search(r"_(\d{3})_", base)
        with open(p, encoding="utf-8", errors="replace") as f:
            txt = f.read()
        reqs = re.findall(r"->\s*(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(\S+)", txt)
        if reqs:
            method, path = reqs[-1]
            op = matcher.match(method, path.split("?")[0])
        else:
            op = "desconhecida"
        kind = "http_5xx" if checker == "main" and status and status.group(1).startswith("5") else f"restler:{checker}"
        res.append({"op": op, "kind": kind, "sig": f"{checker} {status.group(1) if status else ''}".strip(),
                    "example": base})
    return res


def findings_evomaster(run_dir, matcher):
    res = []
    pat = re.compile(r"(?i)(fault|falha)[^\n]*?\b(GET|POST|PUT|PATCH|DELETE)[:\s]+(/\S*)")
    for p in glob.glob(os.path.join(run_dir, "generated_tests", "**", "*.*"), recursive=True):
        if not p.endswith((".java", ".kt", ".py", ".js", ".txt")):
            continue
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = pat.search(line)
                if m:
                    op = matcher.match(m.group(2), m.group(3).rstrip(",;)\"'"))
                    res.append({"op": op, "kind": "evomaster:fault", "sig": norm_sig(line), "example": line.strip()[:300]})
    return res


PARSERS = {"schemathesis": findings_schemathesis, "restler": findings_restler, "evomaster": findings_evomaster}


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=os.path.join(ROOT, "data", "raw"))
    args = ap.parse_args()

    stats_rows, achados_rows = [], []
    relatos = {}  # chave -> linha

    for run_dir in sorted(glob.glob(os.path.join(args.raw, "*__*__rep*"))):
        meta_p = os.path.join(run_dir, "meta.json")
        if not os.path.exists(meta_p):
            print(f"[aviso] sem meta.json em {run_dir}; execução incompleta, ignorada")
            continue
        meta = json.load(open(meta_p))
        spec = load_spec(os.path.join(ROOT, meta["schema_file"]))
        matcher = OpMatcher(spec)
        flows = read_flows(run_dir)
        t0 = meta["start_ts"]

        covered = set()
        first_seen_op = {}
        run_found = {}

        for r in flows:
            op = matcher.match(r["method"], r["path"])
            first_seen_op.setdefault(op, r["ts"] - t0)
            if 200 <= r["status"] < 300:
                covered.add(op)
            if r["status"] >= 500:
                sig = f"{r['status']} " + norm_sig(r.get("resp_body"))
                k = key_of(meta["api"], op, "http_5xx", sig)
                f = run_found.setdefault(k, {"op": op, "kind": "http_5xx", "sig": sig, "first_s": r["ts"] - t0, "count": 0,
                                             "example": f"{r['method']} {r['path']}?{r.get('query','')} body={r.get('req_body','')[:200]}"})
                f["count"] += 1

        for f in PARSERS.get(meta["tool"], lambda *_: [])(run_dir, matcher):
            if f["kind"] == "http_5xx":
                continue  # 5xx é medido de forma uniforme pelo proxy
            k = key_of(meta["api"], f["op"], f["kind"], f["sig"])
            g = run_found.setdefault(k, dict(f, first_s=first_seen_op.get(f["op"]), count=0))
            g["count"] += 1

        valid_ops = [o for o in matcher.ops]
        stats_rows.append({
            "run_id": meta["run_id"], "api": meta["api"], "tool": meta["tool"], "rep": meta["rep"],
            "budget_sec": meta["budget_sec"], "duracao_real_s": round(meta["end_ts"] - t0, 1),
            "requisicoes": len(flows),
            "operacoes_total": len(valid_ops),
            "operacoes_cobertas_2xx": len([o for o in covered if o in valid_ops]),
            "cobertura_operacoes_pct": round(100 * len([o for o in covered if o in valid_ops]) / max(len(valid_ops), 1), 1),
            "respostas_5xx": sum(1 for r in flows if r["status"] >= 500),
        })

        for k, f in run_found.items():
            achados_rows.append({"run_id": meta["run_id"], "api": meta["api"], "tool": meta["tool"], "rep": meta["rep"],
                                 "chave": k, "operacao": f["op"], "tipo": f["kind"], "assinatura": f["sig"],
                                 "primeira_ocorrencia_s": "" if f.get("first_s") is None else round(f["first_s"], 1),
                                 "ocorrencias": f["count"]})
            rel = relatos.setdefault(k, {"chave": k, "api": meta["api"], "operacao": f["op"], "tipo": f["kind"],
                                         "assinatura": f["sig"], "ferramentas": set(), "exemplo": f.get("example", "")})
            rel["ferramentas"].add(meta["tool"])

    os.makedirs(os.path.join(ROOT, "data", "processed"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "data", "validated"), exist_ok=True)
    write_csv(os.path.join(ROOT, "data", "processed", "run_stats.csv"), stats_rows)
    write_csv(os.path.join(ROOT, "data", "processed", "achados_por_execucao.csv"), achados_rows)

    # preserva classificações já feitas
    rel_path = os.path.join(ROOT, "data", "validated", "relatos.csv")
    old = {}
    if os.path.exists(rel_path):
        with open(rel_path, encoding="utf-8") as f:
            old = {r["chave"]: r for r in csv.DictReader(f)}
    rows = []
    for k, r in sorted(relatos.items(), key=lambda kv: (kv[1]["api"], kv[1]["operacao"], kv[1]["tipo"])):
        row = dict(r, ferramentas=";".join(sorted(r["ferramentas"])))
        for c in CLASS_COLS:
            row[c] = old.get(k, {}).get(c, "")
        rows.append(row)
    write_csv(rel_path, rows, fields=["chave", "api", "operacao", "tipo", "assinatura", "ferramentas", "exemplo"] + CLASS_COLS)

    pend = sum(1 for r in rows if not r["classificacao"])
    print(f"{len(stats_rows)} execuções | {len(achados_rows)} achados por execução | {len(rows)} relatos únicos ({pend} sem classificação)")
    print(f"Classifique cada relato em {rel_path} (VP, FP ou INC) e rode analysis/compute_metrics.py")


def write_csv(path, rows, fields=None):
    if not rows and not fields:
        open(path, "w").close()
        return
    fields = fields or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
