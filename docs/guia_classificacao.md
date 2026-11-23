# Guia de classificação dos relatos (estudo piloto)

Piloto de 2026-11-23 (branch `piloto`): VAmPI, 1 repetição, 10 min por ferramenta
(ver `docs/desvios.md`, D15). Este guia cobre os **32 relatos únicos** de
`data/validated/relatos.csv` (Schemathesis: 20, EvoMaster: 9, RESTler: 4; um relato pode ser de mais de uma ferramenta).

> **A coluna `classificacao` de `relatos.csv` é preenchida só pela equipe**, conforme
> `docs/protocolo_validacao.md`. As sugestões abaixo (`sugestao_ia`) ficam num
> arquivo à parte, `data/validated/sugestoes_ia.csv`, e **não são lidas** por
> `extract_findings.py` nem por `compute_metrics.py`. Foram feitas só a partir dos
> logs e relatórios, **sem reproduzir** nenhuma requisição. Contagem das sugestões:
> FP: 18, INC: 2, VP: 12.

## Como usar

1. Suba a API em estado limpo (protocolo, passo 1):
   ```bash
   LOG_DIR=/tmp/val docker compose -p val -f apis/vampi/docker-compose.yml up -d
   curl -fsS http://localhost:8080/createdb
   export TOKEN=$(apis/vampi/get_token.sh | sed 's/^Authorization: Bearer //')
   ```
2. Rode o `curl` do relato. Para relatos com várias linhas de `curl` (sequência do
   RESTler ou teste *stateful*), rode na ordem. Corpos grandes estão em
   `docs/guia_classificacao_corpos/`.
3. Compare com o trecho do `api.log` da execução original (linha de acesso e, nos
   500, o *traceback* registrado logo depois).
4. Entre um relato e outro, recrie a API se a requisição alterar o estado (`down -v` e `up -d`).

**Origem das requisições:** Schemathesis, `curl` do próprio relatório JUnit;
RESTler, a sequência do *bug bucket*; EvoMaster, o teste em
`EvoMaster_faults_Test.java`; `http_5xx`, a primeira resposta 5xx com a mesma
assinatura em `flows.jsonl`. Tokens das execuções originais foram trocados por
`$TOKEN`. O Schemathesis mascara segredos como `[Filtered]`; troque por um valor
qualquer.

## Resumo

| # | chave | operação | tipo | ferramenta(s) | sugestao_ia |
|---|---|---|---|---|---|
| 1 | `748c1261bd53` | `DELETE /users/v1/{username}` | `evomaster:101` | evomaster | FP |
| 2 | `32650435bf7d` | `DELETE /users/v1/{username}` | `schemathesis:ST105` | schemathesis | FP |
| 3 | `8806276ccfa5` | `GET /books/v1/{book_title}` | `evomaster:101` | evomaster | FP |
| 4 | `fd6017d0fef3` | `GET /books/v1/{book_title}` | `schemathesis:ST105` | schemathesis | FP |
| 5 | `e2ef582a61ec` | `GET /books/v1/{book_title}` | `schemathesis:ST108` | schemathesis | FP |
| 6 | `c4ff37a6cddc` | `GET /createdb` | `http_5xx` | evomaster | INC |
| 7 | `ecff568650e1` | `GET /me` | `evomaster:101` | evomaster | FP |
| 8 | `ab80c5353f05` | `GET /me` | `schemathesis:ST105` | schemathesis | FP |
| 9 | `3fdc99bcfb2f` | `GET /users/v1/{username}` | `http_5xx` | restler | VP VAMPI-01 |
| 10 | `eb50f42a0469` | `GET /users/v1/{username}` | `http_5xx` | restler | VP VAMPI-01 |
| 11 | `adefc91931d0` | `GET /users/v1/{username}` | `http_5xx` | schemathesis | VP VAMPI-01 |
| 12 | `c51f9d1f6889` | `GET /users/v1/{username}` | `http_5xx` | schemathesis | VP VAMPI-01 |
| 13 | `2089893ccaa5` | `GET /users/v1/{username}` | `http_5xx` | schemathesis | VP VAMPI-01 |
| 14 | `43434c45ca1a` | `GET /users/v1/{username}` | `http_5xx` | schemathesis | VP VAMPI-01 |
| 15 | `54d6b5d97be4` | `GET /users/v1/{username}` | `http_5xx` | schemathesis | VP VAMPI-01 |
| 16 | `7202155be343` | `GET /users/v1/{username}` | `restler:InvalidValueChecker` | restler | VP VAMPI-01 |
| 17 | `c78369941b69` | `GET /users/v1/{username}` | `schemathesis:ST103` | schemathesis | VP VAMPI-01 |
| 18 | `766bb9b8d25b` | `POST /books/v1` | `evomaster:101` | evomaster | FP |
| 19 | `3bb5b01b73e9` | `POST /books/v1` | `http_5xx` | evomaster;schemathesis | VP (novo; pooling) |
| 20 | `2ae9805c77ca` | `POST /books/v1` | `schemathesis:ST202` | schemathesis | FP |
| 21 | `cfb9ad4f6da3` | `POST /users/v1/login` | `schemathesis:ST202` | schemathesis | FP |
| 22 | `b565d906d1d4` | `POST /users/v1/register` | `evomaster:101` | evomaster | FP |
| 23 | `4267255482ca` | `POST /users/v1/register` | `schemathesis:ST202` | schemathesis | FP |
| 24 | `6060e0c71cbd` | `PUT /users/v1/{username}/email` | `evomaster:101` | evomaster | FP |
| 25 | `e7f456148913` | `PUT /users/v1/{username}/email` | `restler:InvalidValueChecker` | restler | VP VAMPI-07 |
| 26 | `df7e62f18aab` | `PUT /users/v1/{username}/email` | `schemathesis:ST105` | schemathesis | FP |
| 27 | `45bf0905db24` | `PUT /users/v1/{username}/email` | `schemathesis:ST202` | schemathesis | FP |
| 28 | `862b84be1601` | `PUT /users/v1/{username}/password` | `evomaster:101` | evomaster | FP |
| 29 | `9a9f8f8fef96` | `PUT /users/v1/{username}/password` | `schemathesis:ST105` | schemathesis | FP |
| 30 | `d1a7fc15e629` | `PUT /users/v1/{username}/password` | `schemathesis:ST202` | schemathesis | FP |
| 31 | `5180ebae611a` | `Stateful tests` | `schemathesis:ST103` | schemathesis | VP (novo; mesmo do 3bb5b01b73e9) |
| 32 | `cd3f9722b4a9` | `Stateful tests` | `schemathesis:ST302` | schemathesis | INC |

## Relatos

### 1. `748c1261bd53` — DELETE /users/v1/{username} · `evomaster:101`

- **Operação afetada:** `DELETE /users/v1/{username}`
- **Ferramenta(s):** evomaster
- **Assinatura:** `type: validation.response.contenttype.notallowed`
- **Origem da requisição:** teste `EvoMaster_faults_Test.java#test_4_deleteOnV1ReturnsMismatchResponseWithSchema` em `generated_tests/EvoMaster_faults_Test.java`
- **sugestao_ia:** **FP** — 401 sem token devolve application/problem+json (padrão do connexion); a especificação só documenta application/json. Divergência de especificação, sem defeito funcional.

```bash
curl -i --path-as-is -X DELETE http://localhost:8080/users/v1/oVGlNu
```
Trecho de `data/raw/vampi__evomaster__rep1/api.log` (linha 33):

```text
172.19.0.3 - - [23/Nov/2026 12:11:00] "DELETE /users/v1/oVGlNu HTTP/1.1" 401 -
```

### 2. `32650435bf7d` — DELETE /users/v1/{username} · `schemathesis:ST105`

- **Operação afetada:** `DELETE /users/v1/{username}`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `st<n> undocumented content-type`
- **Origem da requisição:** curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)
- **sugestao_ia:** **FP** — Mesma causa do 748c1261bd53: 401 com Content-Type application/problem+json não documentado.

```bash
curl -i --path-as-is -X DELETE http://localhost:8080/users/v1/admin
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 179):

```text
172.19.0.3 - - [23/Nov/2026 12:21:21] "DELETE /users/v1/admin HTTP/1.1" 401 -
```

### 3. `8806276ccfa5` — GET /books/v1/{book_title} · `evomaster:101`

- **Operação afetada:** `GET /books/v1/{book_title}`
- **Ferramenta(s):** evomaster
- **Assinatura:** `type: validation.response.contenttype.notallowed`
- **Origem da requisição:** teste `EvoMaster_faults_Test.java#test_3_getOnV1ReturnsMismatchResponseWithSchema` em `generated_tests/EvoMaster_faults_Test.java`
- **sugestao_ia:** **FP** — 401 com application/problem+json não documentado (mesma causa do 748c1261bd53).

```bash
curl -i --path-as-is -X GET http://localhost:8080/books/v1/bSbQl2
```
Trecho de `data/raw/vampi__evomaster__rep1/api.log` (linha 28):

```text
172.19.0.3 - - [23/Nov/2026 12:11:00] "GET /books/v1/bSbQl2 HTTP/1.1" 401 -
```

### 4. `fd6017d0fef3` — GET /books/v1/{book_title} · `schemathesis:ST105`

- **Operação afetada:** `GET /books/v1/{book_title}`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `st<n> undocumented content-type`
- **Origem da requisição:** curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)
- **sugestao_ia:** **FP** — 401 com application/problem+json não documentado (mesma causa do 748c1261bd53).

```bash
curl -i --path-as-is -X GET http://localhost:8080/books/v1/book99
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 22):

```text
172.19.0.3 - - [23/Nov/2026 12:21:17] "GET /books/v1/book99 HTTP/1.1" 401 -
```

### 5. `e2ef582a61ec` — GET /books/v1/{book_title} · `schemathesis:ST108`

- **Operação afetada:** `GET /books/v1/{book_title}`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `st<n> response violates schema`
- **Origem da requisição:** curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)
- **sugestao_ia:** **FP** — A especificação declara array como resposta 200, mas a API devolve um objeto. Erro na especificação. O livro consultado (book99) é do próprio usuário autenticado (name1), então isso não evidencia o VAMPI-03.

```bash
curl -i --path-as-is -X GET -H "Authorization: Bearer $TOKEN" http://localhost:8080/books/v1/book99
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 21):

```text
172.19.0.3 - - [23/Nov/2026 12:21:17] "GET /books/v1/book99 HTTP/1.1" 200 -
```

### 6. `c4ff37a6cddc` — GET /createdb · `http_5xx`

- **Operação afetada:** `GET /createdb`
- **Ferramenta(s):** evomaster
- **Assinatura:** `500 sqlalchemy.exc.integrityerror: (sqlite<n>.integrityerror) unique constraint failed: books.book_title`
- **Origem da requisição:** primeira resposta 5xx com esta assinatura em `data/raw/vampi__evomaster__rep1/flows.jsonl`
- **sugestao_ia:** **INC** — /createdb dá 500 (IntegrityError) quando o título sorteado colide (ameaça A1). Não reproduz de forma determinística. Exceção não tratada: a equipe decide se é defeito novo.

```bash
curl -i --path-as-is -X GET -H "Authorization: Bearer $TOKEN" http://localhost:8080/createdb
```
Trecho de `data/raw/vampi__evomaster__rep1/api.log` (linha 624):

```text
172.19.0.3 - - [23/Nov/2026 12:11:08] "GET /createdb HTTP/1.1" 500 -
Traceback (trecho):
  File "/vampi/models/user_model.py", line 101, in init_db_users
    User.register_user("admin", "pass1", "admin@mail.com", True)
  File "/vampi/models/user_model.py", line 89, in register_user
    db.session.commit()
...
sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: books.book_title
```

### 7. `ecff568650e1` — GET /me · `evomaster:101`

- **Operação afetada:** `GET /me`
- **Ferramenta(s):** evomaster
- **Assinatura:** `type: validation.response.contenttype.notallowed`
- **Origem da requisição:** teste `EvoMaster_faults_Test.java#test_0_getOnMeReturnsMismatchResponseWithSchema` em `generated_tests/EvoMaster_faults_Test.java`
- **sugestao_ia:** **FP** — 401 com application/problem+json não documentado (mesma causa do 748c1261bd53).

```bash
curl -i --path-as-is -X GET http://localhost:8080/me
```
Trecho de `data/raw/vampi__evomaster__rep1/api.log` (linha 35):

```text
172.19.0.3 - - [23/Nov/2026 12:11:00] "GET /me HTTP/1.1" 401 -
```

### 8. `ab80c5353f05` — GET /me · `schemathesis:ST105`

- **Operação afetada:** `GET /me`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `st<n> undocumented content-type`
- **Origem da requisição:** curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)
- **sugestao_ia:** **FP** — 401 com application/problem+json não documentado (mesma causa do 748c1261bd53).

```bash
curl -i --path-as-is -X GET http://localhost:8080/me
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 140):

```text
172.19.0.3 - - [23/Nov/2026 12:21:21] "GET /me HTTP/1.1" 401 -
```

### 9. `3fdc99bcfb2f` — GET /users/v1/{username} · `http_5xx`

- **Operação afetada:** `GET /users/v1/{username}`
- **Ferramenta(s):** restler
- **Assinatura:** `500 sqlalchemy.exc.statementerror: (sqlalchemy.exc.invalidrequesterror) a value is required for bind parameter 'x<n>bcb'`
- **Origem da requisição:** primeira resposta 5xx com esta assinatura em `data/raw/vampi__restler__rep1/flows.jsonl`
- **sugestao_ia:** **VP VAMPI-01** — O username é concatenado na SQL (users.py:46 → user_model.py:73, text(user_query)); ':X2BCb' vira parâmetro de bind. Evidência de SQL injection.

```bash
curl -i --path-as-is -X GET -H "Authorization: Bearer $TOKEN" 'http://localhost:8080/users/v1/]:X2BCb'
```
Trecho de `data/raw/vampi__restler__rep1/api.log` (linha 781):

```text
172.19.0.3 - - [23/Nov/2026 12:00:39] "GET /users/v1/]:X2BCb HTTP/1.1" 500 -
Traceback (trecho):
  File "/vampi/api_views/users.py", line 46, in get_by_username
    if User.get_user(username):
  File "/vampi/models/user_model.py", line 73, in get_user
    query = db.session.execute(text(user_query))
...
sqlalchemy.exc.StatementError: (sqlalchemy.exc.InvalidRequestError) A value is required for bind parameter 'X2BCb'
```

### 10. `eb50f42a0469` — GET /users/v1/{username} · `http_5xx`

- **Operação afetada:** `GET /users/v1/{username}`
- **Ferramenta(s):** restler
- **Assinatura:** `500 sqlalchemy.exc.operationalerror: (sqlite<n>.operationalerror) near "l$m": syntax error`
- **Origem da requisição:** primeira resposta 5xx com esta assinatura em `data/raw/vampi__restler__rep1/flows.jsonl`
- **sugestao_ia:** **VP VAMPI-01** — Aspa simples no username quebra a SQL (OperationalError syntax error) no mesmo ponto (user_model.py:73).

```bash
curl -i --path-as-is -X GET -H "Authorization: Bearer $TOKEN" 'http://localhost:8080/users/v1/^y'"'"'L$M['"'"'n%]JXSDEh*'
```
Trecho de `data/raw/vampi__restler__rep1/api.log` (linha 974):

```text
172.19.0.3 - - [23/Nov/2026 12:00:39] "GET /users/v1/^y'L$M['n%]JXSDEh* HTTP/1.1" 500 -
Traceback (trecho):
  File "/vampi/api_views/users.py", line 46, in get_by_username
    if User.get_user(username):
  File "/vampi/models/user_model.py", line 73, in get_user
    query = db.session.execute(text(user_query))
...
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) near "L$M": syntax error
```

### 11. `adefc91931d0` — GET /users/v1/{username} · `http_5xx`

- **Operação afetada:** `GET /users/v1/{username}`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `500 sqlalchemy.exc.operationalerror: (sqlite<n>.operationalerror) near "񪪑": syntax error`
- **Origem da requisição:** primeira resposta 5xx com esta assinatura em `data/raw/vampi__schemathesis__rep1/flows.jsonl`
- **sugestao_ia:** **VP VAMPI-01** — Aspa simples no username gera OperationalError na SQL montada por concatenação (user_model.py:73).

```bash
curl -i --path-as-is -X GET -H "Authorization: Bearer $TOKEN" http://localhost:8080/users/v1/%F1%9F%B9%A1%F2%8C%A4%A7%0A%27%F1%AA%AA%91%1A
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 5508):

```text
172.19.0.3 - - [23/Nov/2026 12:22:53] "GET /users/v1/񟹡򌤧%0A'񪪑%1A HTTP/1.1" 500 -
Traceback (trecho):
  File "/vampi/api_views/users.py", line 46, in get_by_username
    if User.get_user(username):
  File "/vampi/models/user_model.py", line 73, in get_user
    query = db.session.execute(text(user_query))
...
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) near "񪪑": syntax error
```

### 12. `c51f9d1f6889` — GET /users/v1/{username} · `http_5xx`

- **Operação afetada:** `GET /users/v1/{username}`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `500 sqlalchemy.exc.operationalerror: (sqlite<n>.operationalerror) unrecognized token: "'񟹡򌤧`
- **Origem da requisição:** primeira resposta 5xx com esta assinatura em `data/raw/vampi__schemathesis__rep1/flows.jsonl`
- **sugestao_ia:** **VP VAMPI-01** — Mesma causa: aspa simples no username, SQL concatenada (user_model.py:73).

```bash
curl -i --path-as-is -X GET -H "Authorization: Bearer $TOKEN" http://localhost:8080/users/v1/%F1%9F%B9%A1%F2%8C%A4%A7%0A%27
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 5997):

```text
172.19.0.3 - - [23/Nov/2026 12:22:54] "GET /users/v1/񟹡򌤧%0A' HTTP/1.1" 500 -
Traceback (trecho):
  File "/vampi/api_views/users.py", line 46, in get_by_username
    if User.get_user(username):
  File "/vampi/models/user_model.py", line 73, in get_user
    query = db.session.execute(text(user_query))
...
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'񟹡򌤧
```

### 13. `2089893ccaa5` — GET /users/v1/{username} · `http_5xx`

- **Operação afetada:** `GET /users/v1/{username}`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `500 sqlalchemy.exc.operationalerror: (sqlite<n>.operationalerror) unrecognized token: "'񟹡򌤧''"`
- **Origem da requisição:** primeira resposta 5xx com esta assinatura em `data/raw/vampi__schemathesis__rep1/flows.jsonl`
- **sugestao_ia:** **VP VAMPI-01** — Mesma causa: aspa simples no username, SQL concatenada (user_model.py:73).

```bash
curl -i --path-as-is -X GET -H "Authorization: Bearer $TOKEN" http://localhost:8080/users/v1/%F1%9F%B9%A1%F2%8C%A4%A7%27
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 6080):

```text
172.19.0.3 - - [23/Nov/2026 12:22:54] "GET /users/v1/񟹡򌤧' HTTP/1.1" 500 -
Traceback (trecho):
  File "/vampi/api_views/users.py", line 46, in get_by_username
    if User.get_user(username):
  File "/vampi/models/user_model.py", line 73, in get_user
    query = db.session.execute(text(user_query))
...
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'񟹡򌤧''"
```

### 14. `43434c45ca1a` — GET /users/v1/{username} · `http_5xx`

- **Operação afetada:** `GET /users/v1/{username}`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `500 sqlalchemy.exc.operationalerror: (sqlite<n>.operationalerror) unrecognized token: "'񟹡''"`
- **Origem da requisição:** primeira resposta 5xx com esta assinatura em `data/raw/vampi__schemathesis__rep1/flows.jsonl`
- **sugestao_ia:** **VP VAMPI-01** — Mesma causa: aspa simples no username, SQL concatenada (user_model.py:73).

```bash
curl -i --path-as-is -X GET -H "Authorization: Bearer $TOKEN" http://localhost:8080/users/v1/%F1%9F%B9%A1%27
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 6159):

```text
172.19.0.3 - - [23/Nov/2026 12:22:54] "GET /users/v1/񟹡' HTTP/1.1" 500 -
Traceback (trecho):
  File "/vampi/api_views/users.py", line 46, in get_by_username
    if User.get_user(username):
  File "/vampi/models/user_model.py", line 73, in get_user
    query = db.session.execute(text(user_query))
...
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'񟹡''"
```

### 15. `54d6b5d97be4` — GET /users/v1/{username} · `http_5xx`

- **Operação afetada:** `GET /users/v1/{username}`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `500 sqlalchemy.exc.operationalerror: (sqlite<n>.operationalerror) unrecognized token: "'''"`
- **Origem da requisição:** primeira resposta 5xx com esta assinatura em `data/raw/vampi__schemathesis__rep1/flows.jsonl`
- **sugestao_ia:** **VP VAMPI-01** — GET /users/v1/' → 500 unrecognized token. Caso mínimo de SQL injection (user_model.py:73).

```bash
curl -i --path-as-is -X GET -H "Authorization: Bearer $TOKEN" http://localhost:8080/users/v1/%27
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 6238):

```text
172.19.0.3 - - [23/Nov/2026 12:22:54] "GET /users/v1/' HTTP/1.1" 500 -
Traceback (trecho):
  File "/vampi/api_views/users.py", line 46, in get_by_username
    if User.get_user(username):
  File "/vampi/models/user_model.py", line 73, in get_user
    query = db.session.execute(text(user_query))
...
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'''"
```

### 16. `7202155be343` — GET /users/v1/{username} · `restler:InvalidValueChecker`

- **Operação afetada:** `GET /users/v1/{username}`
- **Ferramenta(s):** restler
- **Assinatura:** `InvalidValueChecker 500`
- **Origem da requisição:** sequência do *bug bucket* do RESTler (`data/raw/vampi__restler__rep1/Fuzz/RestlerResults/experiment24/bug_buckets/InvalidValueChecker_500_1.replay.txt`)
- **sugestao_ia:** **VP VAMPI-01** — O bucket do RESTler é a mesma requisição do 3fdc99bcfb2f (GET /users/v1/]:X2BCb → 500 na SQL concatenada).

```bash
curl -i --path-as-is -X GET -H "Authorization: Bearer $TOKEN" 'http://localhost:8080/users/v1/]:X2BCb'
```
Trecho de `data/raw/vampi__restler__rep1/api.log` (linha 781):

```text
172.19.0.3 - - [23/Nov/2026 12:00:39] "GET /users/v1/]:X2BCb HTTP/1.1" 500 -
Traceback (trecho):
  File "/vampi/api_views/users.py", line 46, in get_by_username
    if User.get_user(username):
  File "/vampi/models/user_model.py", line 73, in get_user
    query = db.session.execute(text(user_query))
...
sqlalchemy.exc.StatementError: (sqlalchemy.exc.InvalidRequestError) A value is required for bind parameter 'X2BCb'
```

### 17. `c78369941b69` — GET /users/v1/{username} · `schemathesis:ST103`

- **Operação afetada:** `GET /users/v1/{username}`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `st<n> undocumented status code`
- **Origem da requisição:** curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)
- **sugestao_ia:** **VP VAMPI-01** — O status não documentado é o 500 de GET /users/v1/' (SQL injection).

```bash
curl -i --path-as-is -X GET -H "Authorization: Bearer $TOKEN" http://localhost:8080/users/v1/%27
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 6238):

```text
172.19.0.3 - - [23/Nov/2026 12:22:54] "GET /users/v1/' HTTP/1.1" 500 -
Traceback (trecho):
  File "/vampi/api_views/users.py", line 46, in get_by_username
    if User.get_user(username):
  File "/vampi/models/user_model.py", line 73, in get_user
    query = db.session.execute(text(user_query))
...
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'''"
```

### 18. `766bb9b8d25b` — POST /books/v1 · `evomaster:101`

- **Operação afetada:** `POST /books/v1`
- **Ferramenta(s):** evomaster
- **Assinatura:** `type: validation.response.contenttype.notallowed`
- **Origem da requisição:** teste `EvoMaster_faults_Test.java#test_1_postOnV1ReturnsMismatchResponseWithSchema` em `generated_tests/EvoMaster_faults_Test.java`
- **sugestao_ia:** **FP** — 401 com application/problem+json não documentado (mesma causa do 748c1261bd53).

```bash
curl -i --path-as-is -X POST -H 'Content-Type: application/json' -d '{  "book_title" : "lIhzt",  "secret" : "PyKQf2pG8d"  }' http://localhost:8080/books/v1
```
Trecho de `data/raw/vampi__evomaster__rep1/api.log` (linha 29):

```text
172.19.0.3 - - [23/Nov/2026 12:11:00] "POST /books/v1 HTTP/1.1" 401 -
```

### 19. `3bb5b01b73e9` — POST /books/v1 · `http_5xx`

- **Operação afetada:** `POST /books/v1`
- **Ferramenta(s):** evomaster;schemathesis
- **Assinatura:** `500 sqlalchemy.exc.integrityerror: (sqlite<n>.integrityerror) unique constraint failed: books.book_title`
- **Origem da requisição:** primeira resposta 5xx com esta assinatura em `data/raw/vampi__evomaster__rep1/flows.jsonl`
- **sugestao_ia:** **VP (novo; pooling)** — POST /books/v1 com título já existente → 500 IntegrityError não tratada (books.py:37). Não está no oráculo; se confirmado, criar defeito com origem=pooling. Obs.: a API às vezes responde 400 'Book Already exists!' (relato 2ae9805c77ca); conferir por que o 500 ocorre.

```bash
curl -i --path-as-is -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"book_title":"bookTitle79", "secret":"pass1secret"}' http://localhost:8080/books/v1
```
Trecho de `data/raw/vampi__evomaster__rep1/api.log` (linha 138):

```text
172.19.0.3 - - [23/Nov/2026 12:11:02] "POST /books/v1 HTTP/1.1" 500 -
Traceback (trecho):
  File "/vampi/api_views/books.py", line 37, in add_new_book
    db.session.commit()
...
sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: books.book_title
```

### 20. `2ae9805c77ca` — POST /books/v1 · `schemathesis:ST202`

- **Operação afetada:** `POST /books/v1`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `st<n> schema-valid request rejected`
- **Origem da requisição:** curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)
- **sugestao_ia:** **FP** — 400 'Book Already exists!' para um título já existente é a regra de negócio correta. A especificação não documenta o 400.

```bash
curl -i --path-as-is -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"book_title": "book99", "secret": "[Filtered]"}' http://localhost:8080/books/v1
```
O Schemathesis mascara segredos como `[Filtered]` no relatório; troque pelo valor usado (ex.: senha) ou por um valor qualquer.

Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 32):

```text
172.19.0.3 - - [23/Nov/2026 12:21:20] "POST /books/v1 HTTP/1.1" 400 -
```

### 21. `cfb9ad4f6da3` — POST /users/v1/login · `schemathesis:ST202`

- **Operação afetada:** `POST /users/v1/login`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `st<n> schema-valid request rejected`
- **Origem da requisição:** curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)
- **sugestao_ia:** **FP** — Corpo {} é rejeitado com 400 porque a especificação não marca username/password como obrigatórios. Erro na especificação.

```bash
curl -i --path-as-is -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{}' http://localhost:8080/users/v1/login
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 35):

```text
172.19.0.3 - - [23/Nov/2026 12:21:20] "POST /users/v1/login HTTP/1.1" 400 -
```

### 22. `b565d906d1d4` — POST /users/v1/register · `evomaster:101`

- **Operação afetada:** `POST /users/v1/register`
- **Ferramenta(s):** evomaster
- **Assinatura:** `type: validation.response.body.unexpected`
- **Origem da requisição:** teste `EvoMaster_faults_Test.java#test_2_postOnRegisterReturnsMismatchResponseWithSchema` em `generated_tests/EvoMaster_faults_Test.java`
- **sugestao_ia:** **FP** — O 400 do registro traz corpo JSON, mas a especificação não documenta corpo nessa resposta. Erro na especificação.

```bash
curl -i --path-as-is -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{  "password" : "pass1",  "email" : "user@tempmail.com"  }' http://localhost:8080/users/v1/register
```
Trecho de `data/raw/vampi__evomaster__rep1/api.log` (linha 23):

```text
172.19.0.3 - - [23/Nov/2026 12:11:00] "POST /users/v1/register HTTP/1.1" 400 -
```

### 23. `4267255482ca` — POST /users/v1/register · `schemathesis:ST202`

- **Operação afetada:** `POST /users/v1/register`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `st<n> schema-valid request rejected`
- **Origem da requisição:** curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)
- **sugestao_ia:** **FP** — Corpo {} rejeitado com 400; campos obrigatórios não marcados na especificação.

```bash
curl -i --path-as-is -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{}' http://localhost:8080/users/v1/register
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 73):

```text
172.19.0.3 - - [23/Nov/2026 12:21:20] "POST /users/v1/register HTTP/1.1" 400 -
```

### 24. `6060e0c71cbd` — PUT /users/v1/{username}/email · `evomaster:101`

- **Operação afetada:** `PUT /users/v1/{username}/email`
- **Ferramenta(s):** evomaster
- **Assinatura:** `type: validation.response.contenttype.notallowed`
- **Origem da requisição:** teste `EvoMaster_faults_Test.java#test_6_putOnEmailReturnsMismatchResponseWithSchema` em `generated_tests/EvoMaster_faults_Test.java`
- **sugestao_ia:** **FP** — 401 com application/problem+json não documentado (mesma causa do 748c1261bd53).

```bash
curl -i --path-as-is -X PUT -H 'Content-Type: application/json' -d '{  "email" : "_VzuiA08"  }' http://localhost:8080/users/v1/_VzuiA08/email
```
Trecho de `data/raw/vampi__evomaster__rep1/api.log` (linha 32):

```text
172.19.0.3 - - [23/Nov/2026 12:11:00] "PUT /users/v1/_VzuiA08/email HTTP/1.1" 401 -
```

### 25. `e7f456148913` — PUT /users/v1/{username}/email · `restler:InvalidValueChecker`

- **Operação afetada:** `PUT /users/v1/{username}/email`
- **Ferramenta(s):** restler
- **Assinatura:** `InvalidValueChecker`
- **Origem da requisição:** sequência do *bug bucket* do RESTler (`data/raw/vampi__restler__rep1/Fuzz/RestlerResults/experiment24/bug_buckets/InvalidValueChecker_timeout_1.replay.txt`)
- **sugestao_ia:** **VP VAMPI-07** — E-mail longo, só alfanumérico e sem '@', leva a requisição a timeout. Compatível com o ReDoS documentado na validação de e-mail. Conferir reproduzindo e medindo o tempo da resposta.

```bash
curl -i --path-as-is -X PUT -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' --data-binary @docs/guia_classificacao_corpos/e7f456148913.json http://localhost:8080/users/v1/name1/email
```
Trecho do `api.log`: nenhuma linha de acesso com método, caminho e status esperados em `vampi__restler__rep1/api.log` (ex.: requisição que terminou em *timeout*, sem status registrado).

### 26. `df7e62f18aab` — PUT /users/v1/{username}/email · `schemathesis:ST105`

- **Operação afetada:** `PUT /users/v1/{username}/email`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `st<n> undocumented content-type`
- **Origem da requisição:** curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)
- **sugestao_ia:** **FP** — 401 com application/problem+json não documentado (mesma causa do 748c1261bd53).

```bash
curl -i --path-as-is -X PUT -H 'Content-Type: application/json' -d '{"email": "mail3@mail.com"}' http://localhost:8080/users/v1/name1/email
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 25):

```text
172.19.0.3 - - [23/Nov/2026 12:21:17] "PUT /users/v1/name1/email HTTP/1.1" 401 -
```

### 27. `45bf0905db24` — PUT /users/v1/{username}/email · `schemathesis:ST202`

- **Operação afetada:** `PUT /users/v1/{username}/email`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `st<n> schema-valid request rejected`
- **Origem da requisição:** curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)
- **sugestao_ia:** **FP** — Corpo {} rejeitado com 400; campo obrigatório não marcado na especificação.

```bash
curl -i --path-as-is -X PUT -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{}' http://localhost:8080/users/v1/name1/email
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 164):

```text
172.19.0.3 - - [23/Nov/2026 12:21:21] "PUT /users/v1/name1/email HTTP/1.1" 400 -
```

### 28. `862b84be1601` — PUT /users/v1/{username}/password · `evomaster:101`

- **Operação afetada:** `PUT /users/v1/{username}/password`
- **Ferramenta(s):** evomaster
- **Assinatura:** `type: validation.response.contenttype.notallowed`
- **Origem da requisição:** teste `EvoMaster_faults_Test.java#test_5_putOnPasswordReturnsMismatchResponseWithSchema` em `generated_tests/EvoMaster_faults_Test.java`
- **sugestao_ia:** **FP** — 401 com application/problem+json não documentado (mesma causa do 748c1261bd53).

```bash
curl -i --path-as-is -X PUT -H 'Content-Type: application/json' -d '{ }' http://localhost:8080/users/v1/Cw196Twq/password
```
Trecho de `data/raw/vampi__evomaster__rep1/api.log` (linha 31):

```text
172.19.0.3 - - [23/Nov/2026 12:11:00] "PUT /users/v1/Cw196Twq/password HTTP/1.1" 401 -
```

### 29. `9a9f8f8fef96` — PUT /users/v1/{username}/password · `schemathesis:ST105`

- **Operação afetada:** `PUT /users/v1/{username}/password`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `st<n> undocumented content-type`
- **Origem da requisição:** curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)
- **sugestao_ia:** **FP** — 401 com application/problem+json não documentado (mesma causa do 748c1261bd53).

```bash
curl -i --path-as-is -X PUT -H 'Content-Type: application/json' -d '{"password": "[Filtered]"}' http://localhost:8080/users/v1/name1/password
```
O Schemathesis mascara segredos como `[Filtered]` no relatório; troque pelo valor usado (ex.: senha) ou por um valor qualquer.

Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 28):

```text
172.19.0.3 - - [23/Nov/2026 12:21:17] "PUT /users/v1/name1/password HTTP/1.1" 401 -
```

### 30. `d1a7fc15e629` — PUT /users/v1/{username}/password · `schemathesis:ST202`

- **Operação afetada:** `PUT /users/v1/{username}/password`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `st<n> schema-valid request rejected`
- **Origem da requisição:** curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)
- **sugestao_ia:** **FP** — Corpo {} rejeitado com 400; campo obrigatório não marcado na especificação.

```bash
curl -i --path-as-is -X PUT -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{}' http://localhost:8080/users/v1/name1/password
```
Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 168):

```text
172.19.0.3 - - [23/Nov/2026 12:21:21] "PUT /users/v1/name1/password HTTP/1.1" 400 -
```

### 31. `5180ebae611a` — Stateful tests · `schemathesis:ST103`

- **Operação afetada:** `Stateful tests`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `st<n> undocumented status code`
- **Origem da requisição:** curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)
- **sugestao_ia:** **VP (novo; mesmo do 3bb5b01b73e9)** — No teste stateful, o status não documentado é o 500 IntegrityError de POST /books/v1 com título repetido (books.py:37). É o mesmo defeito do 3bb5b01b73e9.

```bash
curl -i --path-as-is -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"": -4.945044658344474e+16, "\u0004\u0089\u00a8\u00a8\uda0b\udfd4|\udaa4\udf89": [], "Infinity": [{"\u0099\ud9e8\udf6f=\u00cb\udba3\udd9a": 27413}], "secret": "[Filtered]", "book_title": "bookTitle67"}' http://localhost:8080/books/v1
```
O Schemathesis mascara segredos como `[Filtered]` no relatório; troque pelo valor usado (ex.: senha) ou por um valor qualquer.

Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 1272):

```text
172.19.0.3 - - [23/Nov/2026 12:21:42] "POST /books/v1 HTTP/1.1" 500 -
Traceback (trecho):
  File "/vampi/api_views/books.py", line 37, in add_new_book
    db.session.commit()
...
sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: books.book_title
```

### 32. `cd3f9722b4a9` — Stateful tests · `schemathesis:ST302`

- **Operação afetada:** `Stateful tests`
- **Ferramenta(s):** schemathesis
- **Assinatura:** `st<n> created resource not found`
- **Origem da requisição:** curl de reprodução do relatório JUnit do Schemathesis (`iter_0/junit-*.xml`)
- **sugestao_ia:** **INC** — Livro criado com book_title vazio não pode ser lido em GET /books/v1/ (caminho vazio). Pode ser falta de validação ou limitação do caminho. Decidir após reproduzir.

```bash
curl -i --path-as-is -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"\\\udb9f\uded7\u00c6\u0004": {}, "book_title": "", "secret": "[Filtered]"}' http://localhost:8080/books/v1
curl -i --path-as-is -X GET -H "Authorization: Bearer $TOKEN" http://localhost:8080/books/v1/
```
O Schemathesis mascara segredos como `[Filtered]` no relatório; troque pelo valor usado (ex.: senha) ou por um valor qualquer.

Trecho de `data/raw/vampi__schemathesis__rep1/api.log` (linha 4930):

```text
172.19.0.3 - - [23/Nov/2026 12:22:45] "GET /books/v1/ HTTP/1.1" 404 -
```
