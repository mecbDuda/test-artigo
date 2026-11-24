#!/usr/bin/env python3
"""Resume dados brutos da campanha para o relatório (RESULTADOS_PARA_ARTIGO.md).

Gera em data/processed/:
  resumo_execucao.csv    datas, duração e limites, a partir de data/raw/*/meta.json
  resumo_recursos.csv    média e pico de CPU/memória por escopo e papel (data/raw/recursos.csv)
                         e, por papel, pico de memória e vezes no limite (data/raw/*/conteineres.tsv)
  vampi_operacoes_exercitadas.csv
                         quantas requisições de cada ferramenta exercitaram as operações dos
                         defeitos documentados do VAmPI não detectados (data/raw/vampi__*/flows.jsonl)

Não altera nada em data/raw/.
Uso: python3 analysis/resumir_execucao.py
"""
import csv
import datetime as dt
import glob
import json
import os
import re
import statistics as st
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "processed")


def escrever(nome, rows):
    with open(os.path.join(OUT, nome), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def execucao():
    metas = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(RAW, "*__*__rep*", "meta.json")))]
    iv = sorted((m["start_ts"], m["end_ts"]) for m in metas)
    ativo, (cs, ce) = 0.0, iv[0]
    for a, b in iv[1:]:
        if a > ce:
            ativo += ce - cs
            cs, ce = a, b
        else:
            ce = max(ce, b)
    ativo += ce - cs
    durs = [m["end_ts"] - m["start_ts"] for m in metas]
    fmt = lambda t: dt.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")
    inc = os.path.join(RAW, "_incompletas")
    rows = [
        ("execucoes_concluidas", len(metas)),
        ("execucoes_incompletas_refeitas", len(os.listdir(inc)) if os.path.isdir(inc) else 0),
        ("inicio_primeira_execucao", fmt(iv[0][0])),
        ("fim_ultima_execucao", fmt(max(b for _, b in iv))),
        ("horas_de_relogio", round((max(b for _, b in iv) - iv[0][0]) / 3600, 2)),
        ("horas_com_execucao_ativa", round(ativo / 3600, 2)),
        ("duracao_execucao_media_s", round(st.mean(durs), 1)),
        ("duracao_execucao_min_s", round(min(durs), 1)),
        ("duracao_execucao_max_s", round(max(durs), 1)),
        ("orcamento_s", metas[0]["budget_sec"]),
        ("slots_paralelos", metas[0]["slots_paralelos"]),
        ("sementes_por_repeticao", " ".join(f"rep{r}={s}" for r, s in sorted({(m["rep"], m["seed"]) for m in metas}))),
    ] + [(f"limite_{k}", v) for k, v in metas[0]["limites"].items()]
    escrever("resumo_execucao.csv", [{"item": k, "valor": v} for k, v in rows])


def recursos():
    rc = list(csv.DictReader(open(os.path.join(RAW, "recursos.csv"), encoding="utf-8")))

    def papel(r):
        if r["escopo"] != "conteiner":
            return "maquina (host WSL)"
        n = r["nome"]
        if n.endswith("-api-1"):
            return "api"
        if n.endswith("-proxy-1"):
            return "proxy"
        return "ferramenta: " + (r["execucao"].split("__")[1] if r["execucao"] else "?")

    g = defaultdict(list)
    for r in rc:
        g[papel(r)].append(r)
    # conteineres.tsv: pico de memória (cgroup) e vezes no limite
    tsv = defaultdict(list)
    for p in glob.glob(os.path.join(RAW, "*__*__rep*", "conteineres.tsv")):
        for r in csv.DictReader(open(p), delimiter="\t"):
            k = r["papel"]
            k = "ferramenta: " + ("schemathesis" if k.startswith("ferramenta:st") else k.split(":")[1].split("_")[0]) \
                if k.startswith("ferramenta") else k
            tsv[k].append(r)
    rows = []
    for k in sorted(g):
        xs = g[k]
        cpu = [float(x["cpu_pct"]) for x in xs if x["cpu_pct"]]
        mem = [float(x["mem_mib"]) for x in xs if x["mem_mib"]]
        mp = [float(x["mem_pct"]) for x in xs if x["mem_pct"]]
        t = tsv.get(k, [])
        rows.append({
            "papel": k, "amostras": len(xs),
            "cpu_media_pct": round(st.mean(cpu), 1), "cpu_pico_pct": round(max(cpu), 1),
            "mem_media_mib": round(st.mean(mem), 1), "mem_pico_mib": round(max(mem), 1),
            "mem_pico_pct_do_limite": round(max(mp), 1),
            "limite_mem_mib": round(float(xs[0]["mem_limite_mib"]), 1) if xs[0]["mem_limite_mib"] else "",
            "conteineres_tsv": len(t),
            "pico_cgroup_mib": round(max(int(r["mem_pico_bytes"] or 0) for r in t) / 2**20, 1) if t else "",
            "vezes_no_limite": sum(int(r["vezes_no_limite"] or 0) for r in t) if t else "",
            "oom_killed": sum(1 for r in t if r["oom_killed"] == "true") if t else "",
        })
    escrever("resumo_recursos.csv", rows)


def vampi():
    regras = [
        ("VAMPI-02", "PUT /users/v1/{outro usuário}/password -> 204",
         lambda m, p, s, b: m == "PUT" and re.match(r"/users/v1/[^/]+/password$", p) and "/name1/" not in p and s == 204),
        ("VAMPI-03", "GET /books/v1/{book_title} -> 200",
         lambda m, p, s, b: m == "GET" and re.match(r"/books/v1/[^/]+$", p) and s == 200),
        ("VAMPI-04", "POST /users/v1/register com campo admin no corpo -> 200",
         lambda m, p, s, b: m == "POST" and p == "/users/v1/register" and "admin" in b and s == 200),
        ("VAMPI-05", "GET /users/v1/_debug -> 200",
         lambda m, p, s, b: m == "GET" and p == "/users/v1/_debug" and s == 200),
        ("VAMPI-06", "POST /users/v1/login -> 400",
         lambda m, p, s, b: m == "POST" and p == "/users/v1/login" and s == 400),
    ]
    c = Counter()
    for f in sorted(glob.glob(os.path.join(RAW, "vampi__*__rep*", "flows.jsonl"))):
        tool = os.path.basename(os.path.dirname(f)).split("__")[1]
        for line in open(f, encoding="utf-8", errors="replace"):
            try:
                o = json.loads(line)
            except ValueError:
                continue
            m, p, s, b = o.get("method", ""), (o.get("path") or "").split("?")[0], o.get("status"), str(o.get("req_body") or "")
            c[(tool, "total")] += 1
            for i, _, fn in regras:
                if fn(m, p, s, b):
                    c[(tool, i)] += 1
    rows = []
    for i, desc, _ in regras:
        rows.append({"defeito_id": i, "requisicao": desc,
                     **{t: c[(t, i)] for t in ("schemathesis", "restler", "evomaster")}})
    rows.append({"defeito_id": "(todas)", "requisicao": "total de requisições nas 3 repetições",
                 **{t: c[(t, "total")] for t in ("schemathesis", "restler", "evomaster")}})
    escrever("vampi_operacoes_exercitadas.csv", rows)


if __name__ == "__main__":
    execucao()
    recursos()
    vampi()
    print("ok: data/processed/resumo_execucao.csv, resumo_recursos.csv, vampi_operacoes_exercitadas.csv")
