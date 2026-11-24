#!/usr/bin/env python3
"""Fase 4: consolida a revisão dos dois avaliadores e atualiza o oráculo.

1. Em data/validated/relatos.csv, onde avaliador_1 e avaliador_2 são "ok",
   classificacao = sugestao e defeito_id = defeito_sugerido. Onde os dois escreveram a
   mesma classificação diferente da sugestão (ex.: "FP" ou "VP NOVO-x-1"), vale essa.
   Os demais casos são divergências: ficam sem classificação e vão para
   data/processed/divergencias.csv, para decisão da equipe.
2. Inclui em data/ground_truth/oraculo.csv, com origem=pooling, os defeitos dos relatos
   classificados como VP que ainda não estão no oráculo (descrição de analysis/sugerir.py).
   As colunas como_reproduzir e verificado dos defeitos novos ficam para a equipe.

Opção --concordancia-total "texto": registra "ok" nas colunas avaliador_1 e avaliador_2
ainda vazias, com o texto em observacoes. Usar só quando a própria equipe declarar que os
dois avaliadores concordam com todas as sugestões (docs/desvios.md, D31).

Uso: python3 analysis/consolidar_revisao.py [--concordancia-total "texto"]
"""
import argparse
import csv
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "analysis"))
import sugerir  # noqa: E402  (descrições dos defeitos sugeridos)

REL = os.path.join(ROOT, "data", "validated", "relatos.csv")
ORAC = os.path.join(ROOT, "data", "ground_truth", "oraculo.csv")
DIV = os.path.join(ROOT, "data", "processed", "divergencias.csv")

# tipo de cada defeito novo (mesmo estilo das categorias do oráculo)
TIPO = {
    "NOVO-vampi-1": "erro_500_restricao_unica",
    "NOVO-vampi-2": "erro_500_intermitente",
    "NOVO-vampi-3": "validacao_entrada",
    "NOVO-catwatch-8": "erro_500_content_type",
    "NOVO-petclinic-rest-1": "erro_500_rota_inexistente",
    "NOVO-petclinic-rest-5": "erro_500_content_type",
    "NOVO-petclinic-rest-6": "erro_500_content_type",
    "NOVO-petclinic-rest-8": "erro_500_estado",
    "NOVO-petclinic-rest-13": "erro_500_estado",
}


# defeitos sem descrição na tabela de analysis/sugerir.py (vêm de regras específicas) ou cujo
# único relato é um teste stateful, sem operação única
EXTRA = {
    "NOVO-vampi-3": ("POST /books/v1; GET /books/v1/{book_title}",
                     "POST /books/v1 aceita book_title vazio e cria um livro que GET /books/v1/{book_title} "
                     "não consegue ler (404)"),
}


def ler(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def escrever(p, rows, fields, fim="\r\n"):
    # relatos.csv sai com CRLF (como no extract_findings.py); o oráculo é mantido com LF
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator=fim)
        w.writeheader()
        w.writerows(rows)


def decisao(cel, r):
    """Normaliza a marcação de um avaliador para (classificacao, defeito)."""
    v = cel.strip()
    if v.lower() == "ok":
        return r["sugestao"].strip().upper(), r["defeito_sugerido"].strip()
    partes = v.split(None, 1)
    c = partes[0].upper() if partes else ""
    d = partes[1].strip() if len(partes) > 1 and c == "VP" else ""
    return c, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--concordancia-total")
    a = ap.parse_args()

    rels = ler(REL)
    fields = list(rels[0].keys())
    if a.concordancia_total:
        for r in rels:
            for col in ("avaliador_1", "avaliador_2"):
                if not r[col].strip():
                    r[col] = "ok"
            if a.concordancia_total not in r["observacoes"]:
                r["observacoes"] = (r["observacoes"] + " | " if r["observacoes"].strip() else "") + a.concordancia_total

    div, n_ok, n_igual = [], 0, 0
    for r in rels:
        a1, a2 = r["avaliador_1"].strip(), r["avaliador_2"].strip()
        if not a1 or not a2:
            div.append({**r, "motivo": "avaliação incompleta"})
            continue
        d1, d2 = decisao(a1, r), decisao(a2, r)
        if d1 == d2 and d1[0] in ("VP", "FP", "INC"):
            r["classificacao"], r["defeito_id"] = d1[0], (d1[1] if d1[0] == "VP" else "")
            if a1.lower() == a2.lower() == "ok":
                n_ok += 1
            else:
                n_igual += 1
        else:
            r["classificacao"], r["defeito_id"] = "", ""
            div.append({**r, "motivo": f"avaliador_1={a1!r}, avaliador_2={a2!r}"})
    escrever(REL, rels, fields)
    escrever(DIV, div, fields + ["motivo"])

    # oráculo: defeitos novos confirmados (VP) que ainda não estão lá
    orac = ler(ORAC)
    ofields = list(orac[0].keys())
    existentes = {o["defeito_id"] for o in orac}
    descr = {i: d for api in sugerir.DEFEITOS for _, _, i, d in sugerir.DEFEITOS[api] if d}
    ops = defaultdict(set)
    api_de = {}
    for r in rels:
        if r["classificacao"] == "VP" and r["defeito_id"]:
            api_de[r["defeito_id"]] = r["api"]
            if "fora da especificação" not in r["operacao"] and r["operacao"] not in ("Stateful tests", "desconhecida"):
                ops[r["defeito_id"]].add(r["operacao"])
    novos = sorted((i for i in api_de if i not in existentes),
                   key=lambda i: (api_de[i], int(i.rsplit("-", 1)[1]) if i.rsplit("-", 1)[1].isdigit() else 0))
    for i in novos:
        if i in EXTRA:
            ops[i] = {EXTRA[i][0]}
            descr.setdefault(i, EXTRA[i][1])
        lista = sorted(ops[i])
        operacao = lista[0] if len(lista) == 1 else (f"(várias: {len(lista)} operações) " + "; ".join(lista[:6])
                                                       + (" …" if len(lista) > 6 else ""))
        orac.append({"defeito_id": i, "api": api_de[i], "operacao": operacao,
                     "tipo": TIPO.get(i, "erro_500_entrada_invalida"), "origem": "pooling",
                     "descricao": descr.get(i, ""), "como_reproduzir": "[preencher]", "verificado": "nao"})
    escrever(ORAC, orac, ofields, "\n")

    c = Counter(r["classificacao"] or "pendente" for r in rels)
    print(f"{len(rels)} relatos: {n_ok} com 'ok' dos dois avaliadores, {n_igual} com a mesma classificação "
          f"diferente da sugestão, {len(div)} divergências ({DIV})")
    print("classificação:", dict(c))
    print(f"oráculo: {len(novos)} defeitos novos com origem=pooling; total {len(orac)}")


if __name__ == "__main__":
    main()
