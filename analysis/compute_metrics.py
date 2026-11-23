#!/usr/bin/env python3
"""
Calcula as métricas do artigo a partir de:
  data/ground_truth/oraculo.csv              defeitos conhecidos (ground truth)
  data/validated/relatos.csv                 relatos classificados (VP / FP / INC)
  data/processed/achados_por_execucao.csv    gerado por extract_findings.py
  data/processed/run_stats.csv               gerado por extract_findings.py

Gera em data/results/:
  metricas_por_execucao.csv, tabela2..tabela6 (.csv) e tabelas.md
  (tabelas no mesmo formato das Tabelas 2 a 6 do artigo).

Definições:
  * Recall    = defeitos do oráculo detectados / defeitos do oráculo da API
  * Precisão  = relatos VP / (relatos VP + relatos FP)  (relatos únicos, INC fora)
  * F1        = média harmônica de precisão e recall
  * TTFF      = segundos até o primeiro achado classificado como VP
  * DPH       = defeitos distintos confirmados / horas de orçamento
"""
import csv
import os
import statistics as st
import sys
from collections import Counter, defaultdict
from itertools import combinations

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_ORDER = ["schemathesis", "restler", "evomaster"]
TOOL_LABEL = {"schemathesis": "Schemathesis", "restler": "RESTler", "evomaster": "EvoMaster (caixa-preta)"}


def read(path):
    if not os.path.exists(path):
        sys.exit(f"Arquivo não encontrado: {path}")
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ids(cell):
    return {x.strip() for x in (cell or "").replace(",", ";").split(";") if x.strip()}


def safe_div(a, b):
    return a / b if b else None


def f1(p, r):
    if p is None or r is None or (p + r) == 0:
        return None if p is None or r is None else 0.0
    return 2 * p * r / (p + r)


def fmt(x, nd=2, pct=False):
    if x is None or x == "":
        return "—"
    return f"{x * 100:.1f}%" if pct else f"{x:.{nd}f}"


def agg(values):
    v = [x for x in values if x is not None]
    if not v:
        return None, None, None, None
    return st.mean(v), st.median(v), min(v), max(v)


def a12(x, y):
    """Vargha-Delaney Â12: probabilidade de um valor de x ser maior que um de y."""
    if not x or not y:
        return None
    more = sum(1 for a in x for b in y if a > b)
    eq = sum(1 for a in x for b in y if a == b)
    return (more + 0.5 * eq) / (len(x) * len(y))


def main():
    oracle = read(os.path.join(ROOT, "data", "ground_truth", "oraculo.csv"))
    relatos = read(os.path.join(ROOT, "data", "validated", "relatos.csv"))
    achados = read(os.path.join(ROOT, "data", "processed", "achados_por_execucao.csv"))
    stats = read(os.path.join(ROOT, "data", "processed", "run_stats.csv"))

    oracle_by_api = defaultdict(set)
    for d in oracle:
        oracle_by_api[d["api"]].add(d["defeito_id"])
    all_oracle_ids = {d["defeito_id"] for d in oracle}

    cls = {r["chave"]: r for r in relatos}
    pend = [r["chave"] for r in relatos if r["classificacao"].strip().upper() not in ("VP", "FP", "INC")]
    if pend:
        print(f"[aviso] {len(pend)} relatos sem classificação válida (VP/FP/INC) serão tratados como INC.")
    unknown = set()
    for r in relatos:
        if r["classificacao"].strip().upper() == "VP":
            if not ids(r["defeito_id"]):
                print(f"[aviso] relato VP {r['chave']} sem defeito_id")
            unknown |= ids(r["defeito_id"]) - all_oracle_ids
    if unknown:
        print(f"[aviso] defeitos VP fora do oráculo (adicione-os ao oraculo.csv com origem=pooling): {sorted(unknown)}")

    ach_by_run = defaultdict(list)
    for a in achados:
        ach_by_run[a["run_id"]].append(a)

    per_run = []
    for s in stats:
        run, api, tool = s["run_id"], s["api"], s["tool"]
        vp_def, vp_rep, fp_rep, inc_rep, ttff = set(), set(), set(), set(), None
        raw = 0
        for a in ach_by_run.get(run, []):
            raw += int(a["ocorrencias"] or 0)
            c = cls.get(a["chave"], {}).get("classificacao", "").strip().upper()
            if c == "VP":
                vp_rep.add(a["chave"]); vp_def |= ids(cls[a["chave"]]["defeito_id"])
                if a["primeira_ocorrencia_s"] != "":
                    t = float(a["primeira_ocorrencia_s"])
                    ttff = t if ttff is None else min(ttff, t)
            elif c == "FP":
                fp_rep.add(a["chave"])
            else:
                inc_rep.add(a["chave"])
        orc = oracle_by_api.get(api, set())
        found = vp_def & orc if orc else vp_def
        rec = safe_div(len(found), len(orc))
        prec = safe_div(len(vp_rep), len(vp_rep) + len(fp_rep))
        per_run.append({
            "run_id": run, "api": api, "tool": tool, "rep": s["rep"],
            "relatos_brutos": raw, "relatos_unicos": len(vp_rep | fp_rep | inc_rep),
            "vp_relatos": len(vp_rep), "fp_relatos": len(fp_rep), "inc_relatos": len(inc_rep),
            "defeitos_detectados": len(found), "defeitos_ids": ";".join(sorted(found)),
            "defeitos_oraculo": len(orc), "fn": len(orc - found) if orc else "",
            "precisao": prec, "recall": rec, "f1": f1(prec, rec),
            "cobertura_operacoes_pct": float(s["cobertura_operacoes_pct"]),
            "requisicoes": int(s["requisicoes"]),
            "ttff_min": None if ttff is None else ttff / 60,
            "dph": len(found) / (int(s["budget_sec"]) / 3600),
        })

    out_dir = os.path.join(ROOT, "data", "results")
    os.makedirs(out_dir, exist_ok=True)
    write(os.path.join(out_dir, "metricas_por_execucao.csv"), per_run)

    tools = [t for t in TOOLS_ORDER if any(r["tool"] == t for r in per_run)] + \
            sorted({r["tool"] for r in per_run} - set(TOOLS_ORDER))
    apis = sorted({r["api"] for r in per_run})
    md = ["# Tabelas geradas automaticamente\n",
          f"Execuções consideradas: {len(per_run)}. Valores de média = média entre repetições.\n"]

    # ---------- Tabela 2: resumo dos relatos (união das repetições) ----------
    t2 = []
    for t in tools:
        runs = [r for r in per_run if r["tool"] == t]
        keys = {a["chave"] for r in runs for a in ach_by_run[r["run_id"]]}
        c = Counter(cls.get(k, {}).get("classificacao", "").strip().upper() or "INC" for k in keys)
        t2.append({"Ferramenta": TOOL_LABEL.get(t, t), "Relatos brutos": sum(r["relatos_brutos"] for r in runs),
                   "Após deduplicação": len(keys), "VP": c["VP"], "FP": c["FP"],
                   "Inconclusivos": len(keys) - c["VP"] - c["FP"]})
    add_table(md, out_dir, "tabela2_resumo_relatos", "Tabela 2 – Resumo dos relatos por ferramenta (união das repetições)", t2)

    # ---------- Tabela 3: defeitos e recall por API (união das repetições) ----------
    t3, union_by = [], {}
    for api in apis + ["Total"]:
        row = {"API": api}
        orc = set().union(*oracle_by_api.values()) if api == "Total" else oracle_by_api.get(api, set())
        row["Defeitos no oráculo"] = len(orc)
        for t in tools:
            runs = [r for r in per_run if r["tool"] == t and (api == "Total" or r["api"] == api)]
            u = set().union(*[ids(r["defeitos_ids"]) for r in runs]) if runs else set()
            union_by[(api, t)] = u
            rec_mean = agg([r["recall"] for r in runs])[0]
            row[f"{TOOL_LABEL.get(t, t)} VP (união)"] = len(u)
            row[f"{TOOL_LABEL.get(t, t)} Recall (união)"] = fmt(safe_div(len(u), len(orc)), pct=True)
            row[f"{TOOL_LABEL.get(t, t)} Recall (média)"] = fmt(rec_mean, pct=True)
        t3.append(row)
    add_table(md, out_dir, "tabela3_recall_por_api", "Tabela 3 – Defeitos detectados e recall por ferramenta e API", t3)

    # ---------- Sobreposição (diagrama de Venn) ----------
    ov = []
    for api in apis:
        found_by = defaultdict(set)
        for t in tools:
            for d in union_by[(api, t)]:
                found_by[d].add(t)
        combos = Counter(" + ".join(TOOL_LABEL.get(t, t) for t in sorted(s, key=tools.index)) for s in found_by.values())
        nenhum = len(oracle_by_api.get(api, set()) - set(found_by))
        for k, v in sorted(combos.items()):
            ov.append({"API": api, "Encontrado por": k, "Defeitos": v})
        ov.append({"API": api, "Encontrado por": "Nenhuma ferramenta", "Defeitos": nenhum})
    add_table(md, out_dir, "sobreposicao_defeitos", "Sobreposição – defeitos por combinação de ferramentas", ov)

    # ---------- Tabela 4: precisão e causas de FP ----------
    t4 = []
    for t in tools:
        keys = {a["chave"] for r in per_run if r["tool"] == t for a in ach_by_run[r["run_id"]]}
        c = Counter(cls.get(k, {}).get("classificacao", "").strip().upper() or "INC" for k in keys)
        fp_types = Counter(cls[k]["tipo"] for k in keys if cls.get(k, {}).get("classificacao", "").strip().upper() == "FP")
        fp_obs = Counter(cls[k]["observacoes"].strip() for k in keys
                         if cls.get(k, {}).get("classificacao", "").strip().upper() == "FP" and cls[k]["observacoes"].strip())
        cause = (fp_obs.most_common(1) or fp_types.most_common(1) or [("—", 0)])[0][0]
        t4.append({"Ferramenta": TOOL_LABEL.get(t, t), "VP": c["VP"], "FP": c["FP"],
                   "Precisão": fmt(safe_div(c["VP"], c["VP"] + c["FP"]), pct=True),
                   "Inconclusivos": len(keys) - c["VP"] - c["FP"], "Principal causa de FP": cause})
    add_table(md, out_dir, "tabela4_precisao", "Tabela 4 – Precisão e relatos inconclusivos por ferramenta", t4)

    # ---------- Tabela 5: P, R, F1 (média das execuções) ----------
    t5 = []
    for t in tools:
        runs = [r for r in per_run if r["tool"] == t]
        p, r_, f = (agg([x[m] for x in runs]) for m in ("precisao", "recall", "f1"))
        t5.append({"Ferramenta": TOOL_LABEL.get(t, t),
                   "Precisão (média)": fmt(p[0], pct=True), "Recall (média)": fmt(r_[0], pct=True),
                   "F1 (média)": fmt(f[0]), "F1 (mín–máx)": f"{fmt(f[2])}–{fmt(f[3])}"})
    add_table(md, out_dir, "tabela5_f1", "Tabela 5 – Precisão, recall e F1-score (média das repetições)", t5)

    # ---------- Tabela 6: exploração e custo ----------
    t6 = []
    for t in tools:
        runs = [r for r in per_run if r["tool"] == t]
        cov, req, tt, dph = (agg([x[m] for x in runs]) for m in ("cobertura_operacoes_pct", "requisicoes", "ttff_min", "dph"))
        t6.append({"Ferramenta": TOOL_LABEL.get(t, t), "Cobertura de operações (%)": fmt(cov[0], 1),
                   "Nº de requisições": fmt(req[0], 0), "TTFF (min)": fmt(tt[0], 1), "DPH": fmt(dph[0])})
    add_table(md, out_dir, "tabela6_custo", "Tabela 6 – Métricas de exploração e custo (média das repetições)", t6)

    # ---------- Comparação estatística (descritiva + Â12) ----------
    comp = []
    for m in ("recall", "precisao", "f1", "cobertura_operacoes_pct", "dph"):
        for a, b in combinations(tools, 2):
            xa = [r[m] for r in per_run if r["tool"] == a and r[m] is not None]
            xb = [r[m] for r in per_run if r["tool"] == b and r[m] is not None]
            row = {"Métrica": m, "Comparação": f"{TOOL_LABEL.get(a, a)} vs {TOOL_LABEL.get(b, b)}",
                   "n": f"{len(xa)}/{len(xb)}", "Â12": fmt(a12(xa, xb)), "p (Mann-Whitney)": "—"}
            try:
                from scipy.stats import mannwhitneyu
                if len(xa) >= 3 and len(xb) >= 3 and len(set(xa + xb)) > 1:
                    row["p (Mann-Whitney)"] = fmt(mannwhitneyu(xa, xb, alternative="two-sided").pvalue, 3)
            except ImportError:
                pass
            comp.append(row)
    add_table(md, out_dir, "comparacao_estatistica", "Comparação par a par (Â12 > 0,5 favorece a primeira ferramenta)", comp)

    with open(os.path.join(out_dir, "tabelas.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Resultados em {out_dir}/ (veja tabelas.md)")


def write(path, rows):
    if not rows:
        open(path, "w").close()
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})


def add_table(md, out_dir, name, title, rows):
    write(os.path.join(out_dir, name + ".csv"), rows)
    md.append(f"\n## {title}\n")
    if not rows:
        md.append("_sem dados_\n")
        return
    cols = list(rows[0].keys())
    md.append("| " + " | ".join(cols) + " |")
    md.append("|" + "---|" * len(cols))
    for r in rows:
        md.append("| " + " | ".join(str(r[c]) for c in cols) + " |")


if __name__ == "__main__":
    main()
