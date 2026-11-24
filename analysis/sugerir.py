#!/usr/bin/env python3
"""Sugere uma classificação (VP/FP/INC) e um defeito para cada relato, como ponto de
partida para a revisão da equipe, e gera o guia de revisão.

Entradas: data/validated/relatos.csv, data/ground_truth/oraculo.csv,
data/processed/reproducao.csv e data/processed/reproducao/<chave>.txt (de
analysis/reproduzir.py), data/processed/reproducao/manual_vampi.txt (reprodução manual
dos casos do VAmPI que dependem de estado) e data/processed/achados_por_execucao.csv.

Saídas:
  - data/validated/relatos.csv: preenche SÓ as colunas sugestao, defeito_sugerido,
    justificativa e reproduzido. As colunas classificacao, defeito_id, avaliador_1 e
    avaliador_2 continuam com o que já estava lá (vazias até a revisão da equipe).
  - docs/guia_revisao.md: relatos agrupados por API e defeito sugerido, com a evidência
    resumida, para os dois avaliadores.

As regras ficam todas neste arquivo (DEFEITOS e classificar()); nada é decidido fora dele.
Uso: python3 analysis/sugerir.py
"""
import csv
import os
import re
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL = os.path.join(ROOT, "data", "validated", "relatos.csv")
ORAC = os.path.join(ROOT, "data", "ground_truth", "oraculo.csv")
REPRO_CSV = os.path.join(ROOT, "data", "processed", "reproducao.csv")
REPRO_DIR = os.path.join(ROOT, "data", "processed", "reproducao")
ACHADOS = os.path.join(ROOT, "data", "processed", "achados_por_execucao.csv")
GUIA = os.path.join(ROOT, "docs", "guia_revisao.md")

# ---------------------------------------------------------------- defeitos
# Critério de agrupamento: um defeito = uma causa no código. Para exceções lançadas pelo
# framework antes de a requisição chegar à lógica da aplicação (tipo inválido, JSON
# malformado, rota inexistente...), um defeito por tipo de exceção. Para exceções da
# própria aplicação, um defeito por ponto do código (primeiro frame da aplicação na pilha,
# levantado nos api.log da campanha), juntando verificações do mesmo método.
# (padrão procurado na evidência, filtro de operação ou None, id, descrição)
DEFEITOS = {
    "vampi": [
        (r"operationalerror|syntax error|unrecognized token|value is required for bind parameter", None,
         "VAMPI-01", None),
        (r"integrityerror.*book_title", r"createdb", "NOVO-vampi-2",
         "GET /createdb devolve 500 (IntegrityError) quando o sorteio dos títulos dos livros iniciais "
         "repete um título; intermitente (8 em 300 chamadas numa API limpa)"),
        (r"integrityerror.*book_title", None, "NOVO-vampi-1",
         "POST /books/v1 com título que já pertence a outro usuário devolve 500 (IntegrityError, "
         "restrição UNIQUE de books.book_title) em vez de 400; no piloto foi registrado como VAMPI-10"),
    ],
    "catwatch": [
        (r"sortby must|limit must|offset must", None, "NOVO-catwatch-1",
         "GET /contributors: ContributorsApi.validate rejeita limit, offset ou sortBy inválidos com "
         "IllegalArgumentException, que não é tratada e vira 500 em vez de 400"),
        (r"unsupportedoperationexception", None, "NOVO-catwatch-2",
         "GET /contributors com combinação de parâmetros não implementada (datas) lança "
         "UnsupportedOperationException e devolve 500"),
        (r"parseexception|unparseable date", None, "NOVO-catwatch-3",
         "GET /contributors com data em formato inválido: ParseException em DateUtil.iso8601, devolve 500 "
         "em vez de 400"),
        (r"illegalargumentexception", r"/languages", "NOVO-catwatch-4",
         "GET /languages com limit/offset negativos: IllegalArgumentException em "
         "LanguageService.filterLanguages, devolve 500"),
        (r"illegalargumentexception", r"/projects", "NOVO-catwatch-5",
         "GET /projects com limit/offset negativos: IllegalArgumentException em "
         "ProjectServiceImpl.findProjects, devolve 500"),
        (r"indexoutofbounds", r"/statistics/projects", "NOVO-catwatch-6",
         "GET /statistics/projects: IndexOutOfBoundsException (subList) em "
         "StatisticsApi.statisticsProjectGet quando há menos dados que o esperado"),
        (r"indexoutofbounds", r"/statistics/contributors", "NOVO-catwatch-7",
         "GET /statistics/contributors: IndexOutOfBoundsException (subList) em "
         "StatisticsApi.statisticsContributorGet quando há menos dados que o esperado"),
        (r"multipartexception", None, "NOVO-catwatch-8",
         "POST /config/scoring.project com Content-Type multipart/form-data sem boundary devolve 500 "
         "(MultipartException) em vez de 400/415"),
    ],
    "petclinic-rest": [
        (r"noresourcefoundexception", None, "NOVO-petclinic-rest-1",
         "Caminho inexistente (ex.: /api/owners/320/?/ ou /api/owners/1/1) devolve 500 "
         "(NoResourceFoundException) em vez de 404: o tratador genérico de exceções transforma tudo em 500"),
        (r"methodargumenttypemismatch", None, "NOVO-petclinic-rest-2",
         "Parâmetro de caminho ou de consulta com tipo inválido (ex.: petId=\"abc\", page=\"x\") devolve 500 "
         "(MethodArgumentTypeMismatchException) em vez de 400"),
        (r"constraintviolationexception", None, "NOVO-petclinic-rest-3",
         "Parâmetro que viola restrição de validação (ex.: id negativo, page/size < mínimo) devolve 500 "
         "(ConstraintViolationException) em vez de 400"),
        (r"httpmessagenotreadable", None, "NOVO-petclinic-rest-4",
         "Corpo JSON malformado ou com tipo errado devolve 500 (HttpMessageNotReadableException) em vez de 400"),
        (r"multipartexception", None, "NOVO-petclinic-rest-5",
         "Requisição com Content-Type multipart/form-data sem boundary devolve 500 (MultipartException) "
         "em vez de 400/415"),
        (r"httpmediatypenotsupported", None, "NOVO-petclinic-rest-6",
         "Content-Type não suportado no corpo devolve 500 (HttpMediaTypeNotSupportedException) em vez de 415"),
        (r"invalidparameterexception", None, "NOVO-petclinic-rest-7",
         "Parâmetro de consulta sem nome (ex.: ?=false) devolve 500 (InvalidParameterException) em vez de 400"),
        (r"objectoptimisticlocking", None, "NOVO-petclinic-rest-8",
         "POST de specialty/vet/visit com \"id\" de entidade inexistente no corpo devolve 500 "
         "(ObjectOptimisticLockingFailureException em ClinicServiceImpl.saveSpecialty/saveVet/saveVisit)"),
        (r"invaliddataaccessapiusage", None, "NOVO-petclinic-rest-9",
         "GET /api/v2/owners e /api/v2/pets com page*size acima de Integer.MAX_VALUE devolvem 500 "
         "(InvalidDataAccessApiUsageException: page offset exceeds Integer.MAX_VALUE)"),
        (r"transactionsystemexception", None, "NOVO-petclinic-rest-10",
         "PUT de owner/pet com campos que violam as validações da entidade só falha no commit: 500 "
         "(TransactionSystemException) em vez de 400"),
        (r"illegalargumentexception", None, "NOVO-petclinic-rest-11",
         "POST /api/users sem papéis (roles) devolve 500 (IllegalArgumentException \"User must have at least a "
         "role set!\" em UserServiceImpl.saveUser) em vez de 400"),
        (r"nullpointerexception", None, "NOVO-petclinic-rest-12",
         "POST /api/users com papel sem nome: NullPointerException em UserServiceImpl.saveUser (Role.getName), 500"),
        (r"objectretrievalfailure", None, "NOVO-petclinic-rest-13",
         "POST /api/visits com petId inexistente devolve 500 (ObjectRetrievalFailureException) em vez de 404/400"),
    ],
}

# Causas de falso positivo (texto curto usado na justificativa e no resumo de causas)
FP = {
    "ctype": "Content-Type da resposta diferente do documentado (padrão do framework); sem falha da API",
    "sem_ctype": "resposta sem corpo/sem Content-Type onde a especificação declara um tipo; sem falha da API",
    "status": "código de status correto para a situação, mas não listado na especificação",
    "schema_resp": "resposta difere do schema documentado (erro da especificação, não da API)",
    "corpo": "corpo de resposta não documentado na especificação",
    "rejeita_valido": "API rejeita com 400 uma entrada que a especificação não restringe (especificação incompleta); 400 é a resposta correta",
    "aceita_invalido": "API tolerante: aceita entrada fora do schema e responde normalmente, sem falha",
    "objeto_invalido": "RESTler (InvalidDynamicObjectChecker, bucket 20x) anexou ?injected_query_string=123 ao "
                       "caminho de um objeto válido e esperava erro; a API ignora o parâmetro desconhecido e "
                       "devolve o objeto (20x), comportamento aceitável",
    "metodo":"método não declarado respondido com 400 em vez de 405; sem falha da API",
    "erro_spring": "endpoint interno /error do Spring Boot exposto pela especificação gerada automaticamente; "
                   "chamado diretamente, sem erro anterior, responde 500 (status 999) por desenho do framework",
}


def ler_csv(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def texto_repro(chave):
    p = os.path.join(REPRO_DIR, chave + ".txt")
    return open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""


def respostas(txt):
    """[(status, corpo)] das respostas da reprodução, na ordem."""
    sec = txt.split("=== reprodução em estado limpo ===")[-1].split("=== log da API")[0]
    out = []
    for m in re.finditer(r"-> (\S+) .*?\n  resposta: (.*?)(?=\n\[tentativa|\Z)", sec, re.S):
        out.append((m.group(1), m.group(2)))
    return out


def trecho(txt):
    if "=== trecho do relatório da ferramenta ===" not in txt:
        return ""
    return txt.split("=== trecho do relatório da ferramenta ===")[1].split("=== reprodução")[0]


def mapear(api, texto, operacao):
    t = texto.lower()
    for pad, op, did, _ in DEFEITOS[api]:
        if re.search(pad, t) and (op is None or re.search(op, operacao + " " + t)):
            return did
    return None


def status_recebido(tr):
    m = re.search(r"Received: (\d{3})", tr) or re.search(r"Response status (\d{3})", tr)
    return int(m.group(1)) if m else None


def classificar(r, rep, txt):
    """Devolve (sugestao, defeito, justificativa)."""
    api, tipo, op = r["api"], r["tipo"], r["operacao"]
    tr = trecho(txt)
    resps = respostas(txt)
    r5 = [b for s, b in resps if s.isdigit() and int(s) >= 500]
    ev500 = " ".join([r["assinatura"] if tipo == "http_5xx" else "", tr, " ".join(r5)])
    if tipo.startswith("restler"):
        ev500 += " " + resposta_original_restler(rep)
        if tipo == "restler:InvalidDynamicObjectChecker" and "500" not in r["assinatura"]:
            return "FP", "", FP["objeto_invalido"]
    st_rec = status_recebido(tr)
    reprod = rep.get("reproduzido") == "sim"

    # --- catwatch: /error e dependências externas
    if api == "catwatch" and re.search(r"\s/error$", op):
        return "FP", "", FP["erro_spring"]
    if api == "catwatch" and ("/fetch" in op or re.search(r"mailsend|mailtrap", ev500.lower())):
        return ("INC", "", "GET /fetch tenta buscar dados no GitHub e enviar e-mail (mailtrap.io); o ambiente do "
                "experimento não tem internet (D08), então a falha (500 MailSendException / timeout) vem da "
                "dependência externa indisponível e não dá para separar defeito da API de efeito do ambiente")

    fam = tipo.split(":")[0]
    cod = tipo.split(":")[1] if ":" in tipo else ""

    # --- relatos de conformidade que não dependem do status (conteúdo/formato)
    if cod in ("ST105",) or "contenttype.notallowed" in r["assinatura"]:
        return "FP", "", FP["ctype"]
    if cod in ("ST104", "ST109") or "body.missing" in r["assinatura"]:
        return "FP", "", FP["sem_ctype"]
    if cod == "ST108" or "body.schema" in r["assinatura"]:
        return "FP", "", FP["schema_resp"]
    if "body.unexpected" in r["assinatura"]:
        return "FP", "", FP["corpo"]
    if cod == "ST202":
        return "FP", "", FP["rejeita_valido"]
    if cod == "ST201":
        return "FP", "", FP["aceita_invalido"]
    if cod == "ST204":
        return "FP", "", FP["metodo"]
    if cod == "ST302" and api == "vampi":
        return ("VP", "NOVO-vampi-3", "POST /books/v1 aceita book_title vazio (200 \"Book has been added\") e o "
                "livro criado não pode ser lido por GET /books/v1/{book_title} (404); reproduzido em API limpa")

    # --- timeout do RESTler no PUT de e-mail = ReDoS documentado
    if api == "vampi" and "email" in op and fam == "restler":
        return ("VP", "VAMPI-07", "RESTler registrou timeout no PUT /users/v1/{username}/email com e-mail longo; "
                "reprodução manual: e-mail com 81 caracteres terminando em '!' leva a API a não responder em 30 s "
                "(ReDoS na validação, VAMPI-07)")

    # --- ST103 / status.unknown com status não-5xx: só documentação
    if (cod == "ST103" or "status.unknown" in r["assinatura"]) and st_rec is not None and st_rec < 500:
        return "FP", "", FP["status"] + f" (recebido {st_rec})"

    # --- 500 com exceção identificável
    did = mapear(api, ev500, op)
    if not did and api == "vampi" and "/createdb" in op and (st_rec or 0) >= 500:
        did = "NOVO-vampi-2"   # única causa de 500 no /createdb (pilha nos api.log e reprodução manual)
    if did:
        if did == "VAMPI-01":
            just = ("500 com erro de sintaxe SQL do SQLite ao usar o username na consulta: o valor é concatenado "
                    "no SQL (injeção de SQL, VAMPI-01); reprodução manual com UNION extrai a senha")
        else:
            desc = next(d for _, _, i, d in DEFEITOS[api] if i == did)
            just = "500: " + desc
        if not reprod:
            just += ". Atenção: não reproduziu em API limpa com a requisição registrada"
        return "VP", did, just

    if fam == "restler" and not r5:
        so = rep.get("status_original", "")
        return ("INC", "", f"replay do RESTler (status original {so or '?'}) não reproduziu 500 em API limpa "
                f"(obtido {rep.get('status_reproduzido') or '?'}) e o bucket não traz a exceção")
    if tipo == "http_5xx" or (st_rec and st_rec >= 500):
        return "INC", "", "500 sem exceção identificável na evidência e sem reprodução que a mostre"
    return "INC", "", "evidência insuficiente para decidir"


# Reprodução manual (data/processed/reproducao/manual_vampi.txt): casos que dependem de
# estado e que a reprodução automática (uma requisição numa API recém-criada) não cobre.
MANUAL = {
    "NOVO-vampi-1": "sim (manual: POST com título de livro de outro usuário → 500 IntegrityError)",
    "NOVO-vampi-2": "sim (manual: 8 de 300 chamadas a /createdb → 500 IntegrityError)",
    "VAMPI-07": "sim (manual: PUT de e-mail longo → sem resposta em 30 s)",
}
# Reproduzidos à mão: três 500 do petclinic-rest cujo ID só existia durante a execução,
# repetidos com ID da carga inicial (manual_petclinic.txt), e o replay d270be035ef1 do
# VAmPI, que dá 500 via curl mas ficou sem resposta no cliente de socket (manual_vampi.txt).
MANUAL_CHAVES = {"8a9977537d56", "8e534942bdf5", "acdcbb1d02f4", "d270be035ef1"}
RAW = os.path.join(ROOT, "data", "raw")


def resposta_original_restler(rep):
    """Respostas 5xx registradas no bucket do RESTler (PREVIOUS RESPONSE), com a exceção."""
    fonte = rep.get("fonte_evidencia", "")
    p = os.path.join(RAW, fonte)
    if not fonte or not os.path.isfile(p):
        return ""
    txt = open(p, encoding="utf-8", errors="replace").read()
    return " ".join(m for m in re.findall(r"PREVIOUS RESPONSE: '(HTTP/1\.1 5\d\d.*)", txt))


def main():
    rels = ler_csv(REL)
    fields = list(rels[0].keys())
    rep = {r["chave"]: r for r in ler_csv(REPRO_CSV)} if os.path.exists(REPRO_CSV) else {}
    orac = {r["defeito_id"]: r for r in ler_csv(ORAC)}
    ach = defaultdict(list)
    for a in ler_csv(ACHADOS):
        ach[a["chave"]].append(a)

    for r in rels:
        rp = rep.get(r["chave"], {})
        txt = texto_repro(r["chave"])
        s, d, j = classificar(r, rp, txt)
        if s == "FP" and r["api"] == "catwatch" and "/error" in r["operacao"] and rp.get("reproduzido") == "não" \
                and "whitelabel" in r["assinatura"]:
            reproduzido = "sim"
            j += ("; reprodução sem Accept: text/html devolve o mesmo 500 em JSON (com Accept: text/html, como no "
                  "teste do EvoMaster, vem a página Whitelabel)")
        elif d in MANUAL or r["chave"] in MANUAL_CHAVES:
            reproduzido = "sim"
            j = j.replace(". Atenção: não reproduziu em API limpa com a requisição registrada",
                          ". Reproduzido à mão (data/processed/reproducao/manual_*.txt)")
        else:
            reproduzido = rp.get("reproduzido", "não") or "não"
        r["sugestao"], r["defeito_sugerido"], r["justificativa"], r["reproduzido"] = s, d, j, reproduzido

    with open(REL, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rels)
    escrever_guia(rels, rep, orac, ach)
    c = Counter((r["api"], r["sugestao"]) for r in rels)
    for k in sorted(c):
        print(k, c[k])


def resumo_evidencia(r, rp, txt):
    """Uma ou duas linhas: a requisição e a resposta da reprodução (ou o trecho da ferramenta)."""
    linhas = []
    sec = txt.split("=== reprodução em estado limpo ===")[-1].split("=== log da API")[0]
    passos = re.findall(r"\[tentativa 1, passo \d+\] (.+)", sec)
    resps = respostas(txt)
    if passos:
        req = passos[-1].strip()
        linhas.append(f"`{req[:150]}`")
        if resps:
            st, corpo = resps[min(len(passos), len(resps)) - 1]
            corpo = re.sub(r"\s+", " ", corpo).strip()
            corpo = re.sub(r"(Bearer )[\w.-]+", r"\1…", corpo)
            linhas.append(f"→ {st} `{corpo[:160]}`" if corpo else f"→ {st}")
    tr = trecho(txt)
    if tr:
        sig = [l.strip() for l in tr.splitlines() if re.match(r"\s*(- ST\d+|// Fault1\d\d|Received:|Documented:)",
                                                               l)]
        if sig:
            linhas.append("ferramenta: " + "; ".join(s[:110] for s in sig[:4]))
    return " ".join(linhas) if linhas else (r["exemplo"][:160] or "(sem evidência textual)")


def escrever_guia(rels, rep, orac, ach):
    descr = {i: d for api in DEFEITOS for _, _, i, d in DEFEITOS[api] if d}
    for k, o in orac.items():
        descr.setdefault(k, o["descricao"])
    por_api = defaultdict(list)
    for r in rels:
        por_api[r["api"]].append(r)

    L = []
    L.append("# Guia de revisão dos relatos\n")
    L.append("Relatos únicos da campanha completa (`data/validated/relatos.csv`), com uma **sugestão** de "
             "classificação feita automaticamente (`analysis/sugerir.py`) a partir da evidência de cada relato "
             "(requisição e resposta registradas, relatório da ferramenta, log da API) e da **reprodução** numa "
             "API limpa (`analysis/reproduzir.py`; evidência completa em `data/processed/reproducao/<chave>.txt`). "
             "A sugestão é só um ponto de partida: quem decide é a equipe.\n")
    L.append("## Como revisar\n")
    L.append("Para cada relato, em `data/validated/relatos.csv`, cada avaliador escreve na **sua** coluna "
             "(`avaliador_1` ou `avaliador_2`), sem olhar a do outro:\n")
    L.append("- **`ok`** se concorda com a sugestão (colunas `sugestao` e `defeito_sugerido`);")
    L.append("- senão, a classificação que considera correta: `VP`, `FP` ou `INC`, seguida do defeito quando for "
             "VP (ex.: `VP NOVO-catwatch-2`, `FP`, `INC`).\n")
    L.append("Não preencha `classificacao` nem `defeito_id`: elas são preenchidas depois, a partir das duas "
             "colunas dos avaliadores (onde os dois escreverem `ok`, vale a sugestão; as divergências são "
             "decididas em conjunto). O campo `observacoes` é livre.\n")
    L.append("Definições usadas nas sugestões:\n")
    L.append("- **VP**: o relato aponta uma falha real da API (ex.: 500 causado por entrada do cliente, "
             "vulnerabilidade, timeout), associada a um defeito do oráculo (`VAMPI-xx`) ou a um defeito novo "
             "(`NOVO-<api>-n`, que entra no oráculo com origem `pooling` se confirmado).")
    L.append("- **FP**: o relato não corresponde a uma falha da API (ex.: diferença entre a API e uma "
             "especificação incompleta, código de status correto mas não documentado, comportamento do "
             "framework).")
    L.append("- **INC**: a evidência não permite decidir (não reproduz, depende do ambiente).\n")
    L.append("Critério de agrupamento em defeitos: um defeito = uma causa no código. Exceções lançadas pelo "
             "framework antes de chegar à lógica da aplicação (tipo inválido, JSON malformado, rota inexistente…) "
             "formam um defeito por tipo de exceção; exceções da própria aplicação, um defeito por ponto do código "
             "(primeiro frame da aplicação na pilha, nos `api.log`), juntando verificações do mesmo método. "
             "Um relato de conformidade com a especificação (ex.: ST103 \"status não documentado\") que "
             "reporta um 500 recebe o defeito desse 500, como no piloto.\n")
    L.append("A coluna `reproduzido` diz se o comportamento relatado se repetiu numa API recém-iniciada, com a "
             "mesma requisição (ou sequência) da evidência. Casos que dependem de estado foram reproduzidos à "
             "mão: três defeitos do VAmPI (`data/processed/reproducao/manual_vampi.txt`) e três 500 do "
             "petclinic-rest cujo ID só existia durante a execução, repetidos com ID da carga inicial "
             "(`data/processed/reproducao/manual_petclinic.txt`). Relatos de conformidade (status ou "
             "Content-Type não documentado) que usavam recursos criados durante a execução às vezes não se "
             "repetem numa API limpa (ex.: 404 em vez de 204); isso não muda a sugestão.\n")

    tot = Counter(r["sugestao"] for r in rels)
    L.append("## Resumo\n")
    L.append("| API | relatos | VP sugeridos | FP sugeridos | INC sugeridos | reproduzidos |")
    L.append("|---|---|---|---|---|---|")
    for api in sorted(por_api):
        xs = por_api[api]
        c = Counter(r["sugestao"] for r in xs)
        L.append(f"| {api} | {len(xs)} | {c['VP']} | {c['FP']} | {c['INC']} | "
                 f"{sum(1 for r in xs if r['reproduzido'] == 'sim')} |")
    L.append(f"| **total** | {len(rels)} | {tot['VP']} | {tot['FP']} | {tot['INC']} | "
             f"{sum(1 for r in rels if r['reproduzido'] == 'sim')} |\n")

    L.append("Pontos que merecem mais atenção na revisão (decisões de critério, não só de evidência):\n")
    L.append("- **catwatch, `/error`**: sugerido FP (artefato do Spring Boot). Se a equipe entender que um endpoint "
             "documentado que responde 500 é defeito, esses relatos passam a VP de um defeito novo.")
    L.append("- **catwatch, `/fetch`**: sugerido INC (depende de GitHub e de servidor de e-mail, inacessíveis no "
             "ambiente isolado).")
    L.append("- **VAmPI, `/createdb`**: sugerido VP (NOVO-vampi-2), embora seja intermitente; no piloto foi INC "
             "porque não tinha sido reproduzido.")
    L.append("- **VAmPI, ST302 (título vazio)**: sugerido VP (NOVO-vampi-3); pode ser visto como lacuna da "
             "especificação, que não proíbe título vazio.")
    L.append("- **petclinic-rest**: quase todos os 500 vêm do mesmo tratador genérico de exceções; o guia separa "
             "um defeito por tipo de exceção. Se a equipe preferir um único defeito \"tratador genérico\", "
             "basta usar o mesmo id nos relatos.\n")

    for api in sorted(por_api):
        xs = por_api[api]
        L.append(f"## {api}\n")
        grupos = defaultdict(list)
        for r in xs:
            causa = re.split(r" \(recebido|; reprodução sem Accept", r["justificativa"])[0]
            g = r["defeito_sugerido"] or f"{r['sugestao']}: " + causa
            grupos[(r["sugestao"], g)].append(r)

        def chave_ordem(k):
            num = re.search(r"(\d+)$", k[1])
            return ({"VP": 0, "INC": 1, "FP": 2}[k[0]], re.sub(r"\d+$", "", k[1]), int(num.group(1)) if num else 0)

        for k in sorted(grupos, key=chave_ordem):
            rs = grupos[k]
            sug, g = k
            n = f"{len(rs)} relato" + ("s" if len(rs) > 1 else "")
            if sug == "VP":
                titulo = f"### {g} — VP sugerido ({n})"
                desc = descr.get(g, "")
            else:
                titulo = f"### {sug} sugerido ({n})"
                desc = "Causa: " + g.split(": ", 1)[1]
            L.append(titulo + "\n")
            if desc:
                L.append(f"{desc}.\n")
            ferr = Counter(t for r in rs for t in r["ferramentas"].split(";"))
            L.append("Ferramentas: " + ", ".join(f"{t} ({n})" for t, n in sorted(ferr.items())) + ".\n")
            L.append("| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |")
            L.append("|---|---|---|---|---|---|")
            for r in sorted(rs, key=lambda r: (r["operacao"], r["tipo"])):
                reps = sorted({(a["tool"], a["rep"]) for a in ach[r["chave"]]})
                fr = ", ".join(f"{t[:2]}{rp}" for t, rp in reps)
                ev = resumo_evidencia(r, rep.get(r["chave"], {}), texto_repro(r["chave"]))
                ev = ev.replace("|", "\\|").replace("\n", " ")
                op = r["operacao"].replace("|", "\\|")
                L.append(f"| `{r['chave']}` | {op} | {r['tipo']} | {fr} | {r['reproduzido']} | {ev} |")
            if sug == "VP":
                L.append("")
                L.append("Justificativa: " + rs[0]["justificativa"] + "\n")
            L.append("")
    L.append("Legenda das repetições: `sc` Schemathesis, `re` RESTler, `ev` EvoMaster, seguido do número da "
             "repetição (ex.: `sc2` = Schemathesis, repetição 2).\n")
    with open(GUIA, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    main()
