# Guia de revisão dos relatos

Relatos únicos da campanha completa (`data/validated/relatos.csv`), com uma **sugestão** de classificação feita automaticamente (`analysis/sugerir.py`) a partir da evidência de cada relato (requisição e resposta registradas, relatório da ferramenta, log da API) e da **reprodução** numa API limpa (`analysis/reproduzir.py`; evidência completa em `data/processed/reproducao/<chave>.txt`). A sugestão é só um ponto de partida: quem decide é a equipe.

## Como revisar

Para cada relato, em `data/validated/relatos.csv`, cada avaliador escreve na **sua** coluna (`avaliador_1` ou `avaliador_2`), sem olhar a do outro:

- **`ok`** se concorda com a sugestão (colunas `sugestao` e `defeito_sugerido`);
- senão, a classificação que considera correta: `VP`, `FP` ou `INC`, seguida do defeito quando for VP (ex.: `VP NOVO-catwatch-2`, `FP`, `INC`).

Não preencha `classificacao` nem `defeito_id`: elas são preenchidas depois, a partir das duas colunas dos avaliadores (onde os dois escreverem `ok`, vale a sugestão; as divergências são decididas em conjunto). O campo `observacoes` é livre.

Definições usadas nas sugestões:

- **VP**: o relato aponta uma falha real da API (ex.: 500 causado por entrada do cliente, vulnerabilidade, timeout), associada a um defeito do oráculo (`VAMPI-xx`) ou a um defeito novo (`NOVO-<api>-n`, que entra no oráculo com origem `pooling` se confirmado).
- **FP**: o relato não corresponde a uma falha da API (ex.: diferença entre a API e uma especificação incompleta, código de status correto mas não documentado, comportamento do framework).
- **INC**: a evidência não permite decidir (não reproduz, depende do ambiente).

Critério de agrupamento em defeitos: um defeito = uma causa no código. Exceções lançadas pelo framework antes de chegar à lógica da aplicação (tipo inválido, JSON malformado, rota inexistente…) formam um defeito por tipo de exceção; exceções da própria aplicação, um defeito por ponto do código (primeiro frame da aplicação na pilha, nos `api.log`), juntando verificações do mesmo método. Um relato de conformidade com a especificação (ex.: ST103 "status não documentado") que reporta um 500 recebe o defeito desse 500, como no piloto.

A coluna `reproduzido` diz se o comportamento relatado se repetiu numa API recém-iniciada, com a mesma requisição (ou sequência) da evidência. Casos que dependem de estado foram reproduzidos à mão: três defeitos do VAmPI (`data/processed/reproducao/manual_vampi.txt`) e três 500 do petclinic-rest cujo ID só existia durante a execução, repetidos com ID da carga inicial (`data/processed/reproducao/manual_petclinic.txt`). Relatos de conformidade (status ou Content-Type não documentado) que usavam recursos criados durante a execução às vezes não se repetem numa API limpa (ex.: 404 em vez de 204); isso não muda a sugestão.

## Resumo

| API | relatos | VP sugeridos | FP sugeridos | INC sugeridos | reproduzidos |
|---|---|---|---|---|---|
| catwatch | 75 | 22 | 51 | 2 | 75 |
| petclinic-rest | 268 | 155 | 113 | 0 | 238 |
| vampi | 47 | 29 | 18 | 0 | 46 |
| **total** | 390 | 206 | 182 | 2 | 359 |

Pontos que merecem mais atenção na revisão (decisões de critério, não só de evidência):

- **catwatch, `/error`**: sugerido FP (artefato do Spring Boot). Se a equipe entender que um endpoint documentado que responde 500 é defeito, esses relatos passam a VP de um defeito novo.
- **catwatch, `/fetch`**: sugerido INC (depende de GitHub e de servidor de e-mail, inacessíveis no ambiente isolado).
- **VAmPI, `/createdb`**: sugerido VP (NOVO-vampi-2), embora seja intermitente; no piloto foi INC porque não tinha sido reproduzido.
- **VAmPI, ST302 (título vazio)**: sugerido VP (NOVO-vampi-3); pode ser visto como lacuna da especificação, que não proíbe título vazio.
- **petclinic-rest**: quase todos os 500 vêm do mesmo tratador genérico de exceções; o guia separa um defeito por tipo de exceção. Se a equipe preferir um único defeito "tratador genérico", basta usar o mesmo id nos relatos.

## catwatch

### NOVO-catwatch-1 — VP sugerido (5 relatos)

GET /contributors: ContributorsApi.validate rejeita limit, offset ou sortBy inválidos com IllegalArgumentException, que não é tratada e vira 500 em vez de 400.

Ferramentas: evomaster (3), restler (4), schemathesis (4).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `37b30380feb5` | GET /contributors | http_5xx | ev1, re1, re2, re3, sc3 | sim | `GET /contributors?organizations=cF&limit=-624336580` → 500 `{"timestamp":1795557778458,"status":500,"error":"Internal Server Error","exception":"java.lang.IllegalArgumentException","message":"limit must be greater than z` |
| `b4982bd20b73` | GET /contributors | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc3 | sim | `GET /contributors?organizations=S&start_date=GDd9kwkQkJoRt_9&sortBy=Tb4anLcL&q=TsryEDr2ohVe` → 500 `{"timestamp":1795557778927,"status":500,"error":"Internal Server Error","exception":"java.lang.IllegalArgumentException","message":"sortBy must be empty or have` |
| `f06007aaf0c6` | GET /contributors | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc1, sc2, sc3 | sim | `GET /contributors?organizations=x0VKJIYgu3fTYybe&limit=683&offset=-1467473265&end_date=&sortBy=njF` → 500 `{"timestamp":1795557779778,"status":500,"error":"Internal Server Error","exception":"java.lang.IllegalArgumentException","message":"offset must be greater than ` |
| `192ae38efbd7` | GET /contributors | restler:InvalidValueChecker | re1, re2, re3 | sim | `GET /contributors?organizations=&limit=1&offset=1&start_date=fuzzstring&end_date=fuzzstring&sortBy=fuzzstring&q=fuzzstring` → 500 `{"timestamp":1795560669319,"status":500,"error":"Internal Server Error","exception":"java.lang.IllegalArgumentException","message":"sortBy must be empty or have` |
| `4b8a0b7a1cb0` | GET /contributors | schemathesis:ST103 | sc1, sc2, sc3 | sim | `GET /contributors?organizations=&limit=-2147483648&offset=-2147483648&start_date=&end_date=&sortBy=&q=` → 500 `{"timestamp":1795557780647,"status":500,"error":"Internal Server Error","exception":"java.lang.IllegalArgumentException","message":"offset must be greater than ` ferramenta: - ST101 Server error; - ST103 Undocumented status code; Received: 500; Documented: 0, 200, 401, 403, 404 |

Justificativa: 500: GET /contributors: ContributorsApi.validate rejeita limit, offset ou sortBy inválidos com IllegalArgumentException, que não é tratada e vira 500 em vez de 400


### NOVO-catwatch-2 — VP sugerido (2 relatos)

GET /contributors com combinação de parâmetros não implementada (datas) lança UnsupportedOperationException e devolve 500.

Ferramentas: evomaster (2), restler (1), schemathesis (1).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `ec8101387618` | GET /contributors | evomaster:101 | ev1, ev2, ev3 | sim | `GET /contributors?organizations=PZAIK7Bd3WC6c&limit=5&offset=170&q=SjLBu6` → 500 `{"timestamp":1795557777698,"status":500,"error":"Internal Server Error","exception":"java.lang.UnsupportedOperationException","message":"this parameter configur` ferramenta: // Fault100. HTTP Status 500.; // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `3e29f2638a28` | GET /contributors | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc1, sc2, sc3 | sim | `GET /contributors?organizations=PZAIK7Bd3WC6c&limit=5&offset=170&q=SjLBu6` → 500 `{"timestamp":1795557779404,"status":500,"error":"Internal Server Error","exception":"java.lang.UnsupportedOperationException","message":"this parameter configur` |

Justificativa: 500: GET /contributors com combinação de parâmetros não implementada (datas) lança UnsupportedOperationException e devolve 500


### NOVO-catwatch-3 — VP sugerido (1 relato)

GET /contributors com data em formato inválido: ParseException em DateUtil.iso8601, devolve 500 em vez de 400.

Ferramentas: evomaster (1), restler (1), schemathesis (1).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `470e1b11aa1b` | GET /contributors | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc1, sc3 | sim | `GET /contributors?organizations=x_LEQnq4q0ON&end_date=BPrgohCU&q=ni5l_VzuiA0` → 500 `{"timestamp":1795557778135,"status":500,"error":"Internal Server Error","exception":"java.lang.RuntimeException","message":"java.text.ParseException: Unparseabl` |

Justificativa: 500: GET /contributors com data em formato inválido: ParseException em DateUtil.iso8601, devolve 500 em vez de 400


### NOVO-catwatch-4 — VP sugerido (4 relatos)

GET /languages com limit/offset negativos: IllegalArgumentException em LanguageService.filterLanguages, devolve 500.

Ferramentas: evomaster (2), restler (2), schemathesis (2).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `4de87042ad4c` | GET /languages | evomaster:101 | ev1, ev2, ev3 | sim | `GET /languages?organizations=DAczzt7oL&limit=-2062237281&offset=737&q=Fgl` → 500 `{"timestamp":1795557904903,"status":500,"error":"Internal Server Error","exception":"java.lang.IllegalArgumentException","message":"-2062237281","path":"/langua` ferramenta: // Fault100. HTTP Status 500.; // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `66f6758d35a4` | GET /languages | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc1, sc2, sc3 | sim | `GET /languages?organizations=DAczzt7oL&limit=-2062237281&offset=737&q=Fgl` → 500 `{"timestamp":1795557905444,"status":500,"error":"Internal Server Error","exception":"java.lang.IllegalArgumentException","message":"-2062237281","path":"/langua` |
| `52398f7469be` | GET /languages | restler:InvalidValueChecker | re1, re2, re3 | sim | `GET /languages?organizations=fuzzstring&limit=-10&offset=1&q=fuzzstring` → 500 `{"timestamp":1795560672869,"status":500,"error":"Internal Server Error","exception":"java.lang.IllegalArgumentException","message":"-10","path":"/languages"}` |
| `502c1c799a48` | GET /languages | schemathesis:ST103 | sc1, sc2, sc3 | sim | `GET /languages?organizations=&limit=-2147483648&offset=-2147483648&q=` → 500 `{"timestamp":1795557906427,"status":500,"error":"Internal Server Error","exception":"java.lang.IllegalArgumentException","message":"-2147483648","path":"/langua` ferramenta: - ST101 Server error; - ST103 Undocumented status code; Received: 500; Documented: 0, 200, 401, 403, 404 |

Justificativa: 500: GET /languages com limit/offset negativos: IllegalArgumentException em LanguageService.filterLanguages, devolve 500


### NOVO-catwatch-5 — VP sugerido (4 relatos)

GET /projects com limit/offset negativos: IllegalArgumentException em ProjectServiceImpl.findProjects, devolve 500.

Ferramentas: evomaster (2), restler (2), schemathesis (2).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `124229ae571d` | GET /projects | evomaster:101 | ev1, ev2, ev3 | sim | `GET /projects?organizations=ORcJECLFTa&limit=916&offset=-1253453003&sortBy=MR` → 500 `{"timestamp":1795557907377,"status":500,"error":"Internal Server Error","exception":"java.lang.IllegalArgumentException","message":"-1253453003","path":"/projec` ferramenta: // Fault100. HTTP Status 500.; // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `c97c9091a49c` | GET /projects | http_5xx | ev1, ev2, re1, re2, re3, sc1, sc2, sc3 | sim | `GET /projects?organizations=ORcJECLFTa&limit=916&offset=-1253453003&sortBy=MR` → 500 `{"timestamp":1795557907939,"status":500,"error":"Internal Server Error","exception":"java.lang.IllegalArgumentException","message":"-1253453003","path":"/projec` |
| `9e2492828e13` | GET /projects | restler:InvalidValueChecker | re1, re2, re3 | sim | `GET /projects?organizations=fuzzstring&limit=-10&offset=1&start_date=2019-06-26T20%3A20%3A39%2B00%3A00&end_date=2019-06-26T20%3A20%3A39%2B00%3A00&sort` → 500 `{"timestamp":1795560673346,"status":500,"error":"Internal Server Error","exception":"java.lang.IllegalArgumentException","message":"-10","path":"/projects"}` |
| `77951ad01e12` | GET /projects | schemathesis:ST103 | sc1, sc2, sc3 | sim | `GET /projects?organizations=&limit=-2147483648&offset=-2147483648&start_date=2000-01-01T00%3A00%3A00Z&end_date=2000-01-01T00%3A00%3A00Z&sortBy=&q=&lan` → 500 `{"timestamp":1795557911833,"status":500,"error":"Internal Server Error","exception":"java.lang.IllegalArgumentException","message":"-2147483648","path":"/projec` ferramenta: - ST101 Server error; - ST103 Undocumented status code; Received: 500; Documented: 0, 200, 401, 403, 404 |

Justificativa: 500: GET /projects com limit/offset negativos: IllegalArgumentException em ProjectServiceImpl.findProjects, devolve 500


### NOVO-catwatch-6 — VP sugerido (2 relatos)

GET /statistics/projects: IndexOutOfBoundsException (subList) em StatisticsApi.statisticsProjectGet quando há menos dados que o esperado.

Ferramentas: evomaster (2), restler (1), schemathesis (1).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `34b5cb7c5fee` | GET /statistics/projects | evomaster:101 | ev1, ev2, ev3 | sim | `GET /statistics/projects?organizations=aS` → 500 `{"timestamp":1795557917329,"status":500,"error":"Internal Server Error","exception":"java.lang.IndexOutOfBoundsException","message":"toIndex = 10","path":"/stat` ferramenta: // Fault100. HTTP Status 500.; // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `f179c91d3181` | GET /statistics/projects | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc1, sc2, sc3 | sim | `GET /statistics/projects?organizations=aS` → 500 `{"timestamp":1795557917838,"status":500,"error":"Internal Server Error","exception":"java.lang.IndexOutOfBoundsException","message":"toIndex = 10","path":"/stat` |

Justificativa: 500: GET /statistics/projects: IndexOutOfBoundsException (subList) em StatisticsApi.statisticsProjectGet quando há menos dados que o esperado


### NOVO-catwatch-7 — VP sugerido (2 relatos)

GET /statistics/contributors: IndexOutOfBoundsException (subList) em StatisticsApi.statisticsContributorGet quando há menos dados que o esperado.

Ferramentas: evomaster (2), restler (1), schemathesis (1).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `12a78e4463fd` | GET /statistics/contributors | evomaster:101 | ev1, ev2, ev3 | sim | `GET /statistics/contributors?organizations=t_Cz1_M` → 500 `{"timestamp":1795557914137,"status":500,"error":"Internal Server Error","exception":"java.lang.IndexOutOfBoundsException","message":"toIndex = 10","path":"/stat` ferramenta: // Fault100. HTTP Status 500.; // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `5e267d4c6545` | GET /statistics/contributors | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc1, sc2, sc3 | sim | `GET /statistics/contributors` → 500 `{"timestamp":1795557914672,"status":500,"error":"Internal Server Error","exception":"java.lang.IndexOutOfBoundsException","message":"toIndex = 10","path":"/stat` |

Justificativa: 500: GET /statistics/contributors: IndexOutOfBoundsException (subList) em StatisticsApi.statisticsContributorGet quando há menos dados que o esperado


### NOVO-catwatch-8 — VP sugerido (2 relatos)

POST /config/scoring.project com Content-Type multipart/form-data sem boundary devolve 500 (MultipartException) em vez de 400/415.

Ferramentas: schemathesis (2).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `ee9831c5645a` | POST /config/scoring.project | http_5xx | sc1, sc2, sc3 | sim | `POST /config/scoring.project` → 500 `{"timestamp":1795557998298,"status":500,"error":"Internal Server Error","exception":"org.springframework.web.multipart.MultipartException","message":"Could not ` |
| `3c8694cfe376` | POST /config/scoring.project | schemathesis:ST102 | sc1, sc2, sc3 | sim | `POST /config/scoring.project` → 500 `{"timestamp":1795560673761,"status":500,"error":"Internal Server Error","exception":"org.springframework.web.multipart.MultipartException","message":"Could not ` ferramenta: - ST102 Server error on undeclared request Content-Type |

Justificativa: 500: POST /config/scoring.project com Content-Type multipart/form-data sem boundary devolve 500 (MultipartException) em vez de 400/415


### INC sugerido (2 relatos)

Causa: GET /fetch tenta buscar dados no GitHub e enviar e-mail (mailtrap.io); o ambiente do experimento não tem internet (D08), então a falha (500 MailSendException / timeout) vem da dependência externa indisponível e não dá para separar defeito da API de efeito do ambiente.

Ferramentas: evomaster (2), restler (1).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `fb83972a7613` | GET /fetch | evomaster:101 | ev1, ev2, ev3 | sim | `GET /fetch` → None `TIMEOUT (30 s)` ferramenta: // Fault100. HTTP Status 500.; // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `e4b8736da978` | GET /fetch | http_5xx | ev1, ev2, ev3, re1, re2, re3 | sim | `GET /fetch` → None `TIMEOUT (30 s)` |

### FP sugerido (4 relatos)

Causa: API rejeita com 400 uma entrada que a especificação não restringe (especificação incompleta); 400 é a resposta correta.

Ferramentas: schemathesis (4).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `2dc770fac8a9` | GET /statistics | schemathesis:ST202 | sc1, sc2, sc3 | sim | `GET /statistics?organizations=&start_date=&end_date=` → 400 `Invalid date format for stardDate` ferramenta: - ST202 Schema-valid request rejected; - ST103 Undocumented status code; Received: 400; Documented: 0, 200, 401, 403, 404 |
| `23eb1520ce05` | GET /statistics/contributors | schemathesis:ST202 | sc1, sc2, sc3 | sim | `GET /statistics/contributors?organizations=&start_date=&end_date=` → 400 `Couldn't parse date string .` ferramenta: - ST202 Schema-valid request rejected; - ST103 Undocumented status code; Received: 400; Documented: 200, 401, 403, 404 |
| `b232363973cc` | GET /statistics/languages | schemathesis:ST202 | sc1, sc2, sc3 | sim | `GET /statistics/languages?organizations=&start_date=&end_date=` → 400 `Couldn't parse date string .` ferramenta: - ST202 Schema-valid request rejected; - ST103 Undocumented status code; Received: 400; Documented: 200, 401, 403, 404 |
| `cd5d068caae9` | GET /statistics/projects | schemathesis:ST202 | sc1, sc2, sc3 | sim | `GET /statistics/projects?organizations=&start_date=&end_date=` → 400 `Couldn't parse date string .` ferramenta: - ST202 Schema-valid request rejected; - ST103 Undocumented status code; Received: 400; Documented: 200, 401, 403, 404 |

### FP sugerido (2 relatos)

Causa: API tolerante: aceita entrada fora do schema e responde normalmente, sem falha.

Ferramentas: schemathesis (2).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `e0c762cc4b9b` | GET /languages | schemathesis:ST201 | sc1 | sim | `GET /languages?=false` → 200 `[]` ferramenta: - ST201 Schema-violating request accepted |
| `7048cec42f73` | GET /projects | schemathesis:ST201 | sc3 | sim | `GET /projects?start_date=` → 200 `[]` ferramenta: - ST201 Schema-violating request accepted |

### FP sugerido (4 relatos)

Causa: corpo de resposta não documentado na especificação.

Ferramentas: evomaster (4).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `e4b6011107ed` | GET /delete | evomaster:101 | ev1, ev2, ev3 | sim | `GET /delete` → 401 `{"error":"unauthorized","error_description":"Full authentication is required to access this resource"}` ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `9ef1ed7d0d54` | GET /init | evomaster:101 | ev1, ev2, ev3 | sim | `GET /init` → 401 `{"error":"unauthorized","error_description":"Full authentication is required to access this resource"}` ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `75cb37af20cc` | POST /config/scoring.project | evomaster:101 | ev1, ev2, ev3 | sim | `POST /config/scoring.project` → 403 `This endpoint is deactivated.` ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `5ef79b5b13c0` | POST /import | evomaster:101 | ev1, ev2, ev3 | sim | `POST /import` → 403 `This endpoint is deactivated.` ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |

### FP sugerido (7 relatos)

Causa: código de status correto para a situação, mas não listado na especificação.

Ferramentas: evomaster (2), schemathesis (5).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `b44aa569de27` | GET /statistics | evomaster:101 | ev1, ev2, ev3 | sim | `GET /statistics?start_date=idBv` → 400 `Invalid date format for stardDate` ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `dda44d4e9ea0` | GET /statistics | schemathesis:ST103 | sc1, sc2, sc3 | sim | `GET /statistics?organizations=&start_date=&end_date=` → 400 `Invalid date format for stardDate` ferramenta: - ST202 Schema-valid request rejected; - ST103 Undocumented status code; Received: 400; Documented: 0, 200, 401, 403, 404 |
| `d99dbfdba6e4` | GET /statistics/contributors | schemathesis:ST103 | sc1, sc2, sc3 | sim | `GET /statistics/contributors?organizations=&start_date=&end_date=` → 400 `Couldn't parse date string .` ferramenta: - ST202 Schema-valid request rejected; - ST103 Undocumented status code; Received: 400; Documented: 200, 401, 403, 404 |
| `e92515c0f8eb` | GET /statistics/languages | evomaster:101 | ev1, ev2, ev3 | sim | `GET /statistics/languages?organizations=OZ5ORpdF&end_date=g5dcVW4` → 400 `Couldn't parse date string g5dcVW4.` ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `a61f4e23ad79` | GET /statistics/languages | schemathesis:ST103 | sc1, sc2, sc3 | sim | `GET /statistics/languages?organizations=&start_date=&end_date=` → 400 `Couldn't parse date string .` ferramenta: - ST202 Schema-valid request rejected; - ST103 Undocumented status code; Received: 400; Documented: 200, 401, 403, 404 |
| `629dae2c69fd` | GET /statistics/projects | schemathesis:ST103 | sc1, sc2, sc3 | sim | `GET /statistics/projects?organizations=&start_date=&end_date=` → 400 `Couldn't parse date string .` ferramenta: - ST202 Schema-valid request rejected; - ST103 Undocumented status code; Received: 400; Documented: 200, 401, 403, 404 |
| `e350fef14fd4` | POST /import | schemathesis:ST103 | sc1, sc2, sc3 | sim | `POST /import` → 400 `{"timestamp":1795558101250,"status":400,"error":"Bad Request","exception":"org.springframework.http.converter.HttpMessageNotReadableException","message":"Requir` ferramenta: - ST103 Undocumented status code; Received: 400; Documented: 200, 201, 401, 403, 404 |

### FP sugerido (32 relatos)

Causa: endpoint interno /error do Spring Boot exposto pela especificação gerada automaticamente; chamado diretamente, sem erro anterior, responde 500 (status 999) por desenho do framework.

Ferramentas: evomaster (13), restler (6), schemathesis (20).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `bec072cea103` | DELETE /error | evomaster:101 | ev1, ev2, ev3 | sim | `DELETE /error` → 500 `<html><body><h1>Whitelabel Error Page</h1><p>This application has no explicit mapping for /error, so you are seeing this as a fallback.</p><div id='created'>Tue` ferramenta: // Fault100. HTTP Status 500.; // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `deb30689dd16` | DELETE /error | http_5xx | ev1, ev2, ev3 | sim | `DELETE /error` → 500 `{"timestamp":1795557723868,"status":999,"error":"None","message":"No message available"}` |
| `ce293b122b71` | DELETE /error | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `DELETE /error` → 500 `{"timestamp":1795557738681,"status":999,"error":"None","message":"No message available"}` |
| `7c9f14c9dce9` | DELETE /error | schemathesis:ST103 | sc1, sc2, sc3 | sim | `DELETE /error` → 500 `{"timestamp":1795557750360,"status":999,"error":"None","message":"No message available"}` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/json;charset=UTF-8; Documented: text/html |
| `51cd57fe707a` | DELETE /error | schemathesis:ST105 | sc1, sc2, sc3 | sim | `DELETE /error` → 500 `{"timestamp":1795557762177,"status":999,"error":"None","message":"No message available"}` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/json;charset=UTF-8; Documented: text/html |
| `99e929b009d8` | GET /error | evomaster:101 | ev1, ev2, ev3 | sim | `GET /error` → 500 `<html><body><h1>Whitelabel Error Page</h1><p>This application has no explicit mapping for /error, so you are seeing this as a fallback.</p><div id='created'>Tue` ferramenta: // Fault100. HTTP Status 500.; // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `74deaf12ef2b` | GET /error | http_5xx | ev1, ev2, ev3 | sim | `GET /error` → 500 `{"timestamp":1795557782462,"status":999,"error":"None","message":"No message available"}` |
| `6c9c15b36c08` | GET /error | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `GET /error` → 500 `{"timestamp":1795557782894,"status":999,"error":"None","message":"No message available"}` |
| `8c75e023d692` | GET /error | schemathesis:ST103 | sc1, sc2, sc3 | sim | `GET /error` → 500 `{"timestamp":1795557783489,"status":999,"error":"None","message":"No message available"}` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/json;charset=UTF-8; Documented: text/html |
| `e72b557f7845` | GET /error | schemathesis:ST105 | sc1, sc2, sc3 | sim | `GET /error` → 500 `{"timestamp":1795557784068,"status":999,"error":"None","message":"No message available"}` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/json;charset=UTF-8; Documented: text/html |
| `b6d4cbc33fe5` | HEAD /error | evomaster:101 | ev1, ev2, ev3 | sim | `HEAD /error` → 500 ferramenta: // Fault100. HTTP Status 500.; // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `d35398c0612b` | HEAD /error | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc1, sc2, sc3 | sim | `HEAD /error` → 500 |
| `4fbe92dd4688` | HEAD /error | schemathesis:ST103 | sc1, sc2, sc3 | sim | `HEAD /error` → 500 ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/json;charset=UTF-8; Documented: text/html |
| `46f589aaccc8` | HEAD /error | schemathesis:ST105 | sc1, sc2, sc3 | sim | `HEAD /error` → 500 ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/json;charset=UTF-8; Documented: text/html |
| `21e96a5d5286` | OPTIONS /error | evomaster:101 | ev1, ev2, ev3 | sim | `OPTIONS /error` → 200 ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `2adbbb924e31` | OPTIONS /error | schemathesis:ST104 | sc1, sc2, sc3 | sim | `OPTIONS /error` → 200 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `69f81bea2288` | OPTIONS /error | schemathesis:ST109 | sc1, sc2, sc3 | sim | `OPTIONS /error` → 200 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `6457ac95bae7` | PATCH /error | evomaster:101 | ev1, ev2, ev3 | sim | `PATCH /error` → 500 `<html><body><h1>Whitelabel Error Page</h1><p>This application has no explicit mapping for /error, so you are seeing this as a fallback.</p><div id='created'>Tue` ferramenta: // Fault100. HTTP Status 500.; // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `1d73f5c63b32` | PATCH /error | http_5xx | ev1, ev2, ev3 | sim | `PATCH /error` → 500 `{"timestamp":1795557933958,"status":999,"error":"None","message":"No message available"}` |
| `b171a135b41f` | PATCH /error | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `PATCH /error` → 500 `{"timestamp":1795557948684,"status":999,"error":"None","message":"No message available"}` |
| `c3f7de90e8dc` | PATCH /error | schemathesis:ST103 | sc1, sc2, sc3 | sim | `PATCH /error` → 500 `{"timestamp":1795557960255,"status":999,"error":"None","message":"No message available"}` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/json;charset=UTF-8; Documented: text/html |
| `e07f75ef9947` | PATCH /error | schemathesis:ST105 | sc1, sc2, sc3 | sim | `PATCH /error` → 500 `{"timestamp":1795557971918,"status":999,"error":"None","message":"No message available"}` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/json;charset=UTF-8; Documented: text/html |
| `f30ace1f4b32` | POST /error | evomaster:101 | ev1, ev2, ev3 | sim | `POST /error` → 500 `<html><body><h1>Whitelabel Error Page</h1><p>This application has no explicit mapping for /error, so you are seeing this as a fallback.</p><div id='created'>Tue` ferramenta: // Fault100. HTTP Status 500.; // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `70b9e4462016` | POST /error | http_5xx | ev1, ev2, ev3 | sim | `POST /error` → 500 `{"timestamp":1795558036181,"status":999,"error":"None","message":"No message available"}` |
| `fc0f68fdd98b` | POST /error | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `POST /error` → 500 `{"timestamp":1795558047958,"status":999,"error":"None","message":"No message available"}` |
| `8d9f7ca6fc04` | POST /error | schemathesis:ST103 | sc1, sc2, sc3 | sim | `POST /error` → 500 `{"timestamp":1795558062464,"status":999,"error":"None","message":"No message available"}` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/json;charset=UTF-8; Documented: text/html |
| `86f58bbfe2d7` | POST /error | schemathesis:ST105 | sc1, sc2, sc3 | sim | `POST /error` → 500 `{"timestamp":1795558074254,"status":999,"error":"None","message":"No message available"}` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/json;charset=UTF-8; Documented: text/html |
| `b73f60144385` | PUT /error | evomaster:101 | ev1, ev2, ev3 | sim | `PUT /error` → 500 `<html><body><h1>Whitelabel Error Page</h1><p>This application has no explicit mapping for /error, so you are seeing this as a fallback.</p><div id='created'>Tue` ferramenta: // Fault100. HTTP Status 500.; // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `f1c192783d71` | PUT /error | http_5xx | ev1, ev2, ev3 | sim | `PUT /error` → 500 `{"timestamp":1795558127627,"status":999,"error":"None","message":"No message available"}` |
| `c28ebc6c469d` | PUT /error | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `PUT /error` → 500 `{"timestamp":1795558139445,"status":999,"error":"None","message":"No message available"}` |
| `ff7d15001232` | PUT /error | schemathesis:ST103 | sc1, sc2, sc3 | sim | `PUT /error` → 500 `{"timestamp":1795558151151,"status":999,"error":"None","message":"No message available"}` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/json;charset=UTF-8; Documented: text/html |
| `450f4437eed8` | PUT /error | schemathesis:ST105 | sc1, sc2, sc3 | sim | `PUT /error` → 500 `{"timestamp":1795558165791,"status":999,"error":"None","message":"No message available"}` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/json;charset=UTF-8; Documented: text/html |

### FP sugerido (2 relatos)

Causa: resposta difere do schema documentado (erro da especificação, não da API).

Ferramentas: evomaster (1), schemathesis (1).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `7009bf2d4d0c` | GET /config | evomaster:101 | ev1, ev2, ev3 | sim | `GET /config` → 200 `{"cache.path":"target/cache","cache.size":"50","endpoints.enabled":"false","endpoints.health.enabled":"true","github.login":null,"organization.list":"zalando,za` ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `c8b8dacd4336` | GET /config | schemathesis:ST108 | sc1, sc2, sc3 | sim | `GET /config` → 200 `{"cache.path":"target/cache","cache.size":"50","endpoints.enabled":"false","endpoints.health.enabled":"true","github.login":null,"organization.list":"zalando,za` ferramenta: - ST108 Response violates schema |

## petclinic-rest

### NOVO-petclinic-rest-1 — VP sugerido (39 relatos)

Caminho inexistente (ex.: /api/owners/320/?/ ou /api/owners/1/1) devolve 500 (NoResourceFoundException) em vez de 404: o tratador genérico de exceções transforma tudo em 500.

Ferramentas: restler (39).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `5c10bb29d699` | DELETE /api/owners/{ownerId} | http_5xx | re1, re2, re3 | sim | `DELETE /petclinic/api/owners/320/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/320/","status":500,"title":"NoResourceFoundException","` |
| `ee5970de7142` | DELETE /api/owners/{ownerId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | sim | `DELETE /petclinic/api/owners/320/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/320/","status":500,"title":"NoResourceFoundException","` |
| `f2d1fe4dc719` | DELETE /api/pettypes/{petTypeId} | http_5xx | re1, re2, re3 | sim | `DELETE /petclinic/api/pettypes/212/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/212/","status":500,"title":"NoResourceFoundException"` |
| `35cf475e2b83` | DELETE /api/pettypes/{petTypeId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | sim | `DELETE /petclinic/api/pettypes/212/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/212/","status":500,"title":"NoResourceFoundException"` |
| `4b724c7a877c` | DELETE /api/specialties/{specialtyId} | http_5xx | re1, re2, re3 | sim | `DELETE /petclinic/api/specialties/225/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/225/","status":500,"title":"NoResourceFoundExcepti` |
| `5b87acff7037` | DELETE /api/specialties/{specialtyId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | sim | `DELETE /petclinic/api/specialties/225/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/225/","status":500,"title":"NoResourceFoundExcepti` |
| `c9186b90e34b` | DELETE /api/vets/{vetId} | http_5xx | re1, re2, re3 | sim | `DELETE /petclinic/api/vets/598/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/598/","status":500,"title":"NoResourceFoundException","ty` |
| `dbf2e283e9e8` | DELETE /api/vets/{vetId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | sim | `DELETE /petclinic/api/vets/598/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/598/","status":500,"title":"NoResourceFoundException","ty` |
| `1342828fc641` | DELETE /petclinic/api/owners/{n}/{n} (fora da especificação) | http_5xx | re1, re2, re3 | sim | `DELETE /petclinic/api/owners/320/320` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/320/320","status":500,"title":"NoResourceFoundException` |
| `7b580c980f34` | DELETE /petclinic/api/pettypes/{n}/{n} (fora da especificação) | http_5xx | re1, re2, re3 | sim | `DELETE /petclinic/api/pettypes/212/212` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/212/212","status":500,"title":"NoResourceFoundExcepti` |
| `398512cabbd2` | DELETE /petclinic/api/specialties/{n}/{n} (fora da especificação) | http_5xx | re1, re2, re3 | sim | `DELETE /petclinic/api/specialties/225/225` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/225/225","status":500,"title":"NoResourceFoundExce` |
| `022dfc01a3d2` | DELETE /petclinic/api/vets/{n}/{n} (fora da especificação) | http_5xx | re1, re2, re3 | sim | `DELETE /petclinic/api/vets/598/598` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/598/598","status":500,"title":"NoResourceFoundException",` |
| `8d46bc789c41` | GET /api/owners/{ownerId} | http_5xx | re1, re2, re3 | sim | `GET /petclinic/api/owners/235/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/235/","status":500,"title":"NoResourceFoundException","` |
| `e3efaf18a8dd` | GET /api/owners/{ownerId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | sim | `GET /petclinic/api/owners/235/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/235/","status":500,"title":"NoResourceFoundException","` |
| `0eb8dc32d867` | GET /api/pettypes/{petTypeId} | http_5xx | re1, re2, re3 | sim | `GET /petclinic/api/pettypes/160/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/160/","status":500,"title":"NoResourceFoundException"` |
| `cf16b773f748` | GET /api/pettypes/{petTypeId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | sim | `GET /petclinic/api/pettypes/160/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/160/","status":500,"title":"NoResourceFoundException"` |
| `a7f4ae3f360f` | GET /api/specialties/{specialtyId} | http_5xx | re1, re2, re3 | sim | `GET /petclinic/api/specialties/174/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/174/","status":500,"title":"NoResourceFoundExcepti` |
| `65910127a3ad` | GET /api/specialties/{specialtyId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | sim | `GET /petclinic/api/specialties/174/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/174/","status":500,"title":"NoResourceFoundExcepti` |
| `ebd804fee4b8` | GET /api/vets/{vetId} | http_5xx | re1, re2, re3 | sim | `GET /petclinic/api/vets/571/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/571/","status":500,"title":"NoResourceFoundException","ty` |
| `355e282cd3a7` | GET /api/vets/{vetId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | sim | `GET /petclinic/api/vets/571/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/571/","status":500,"title":"NoResourceFoundException","ty` |
| `c93b8f62eaca` | GET /petclinic/api/owners/{n}/{n} (fora da especificação) | http_5xx | re1, re2, re3 | sim | `GET /petclinic/api/owners/235/235` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/235/235","status":500,"title":"NoResourceFoundException` |
| `7283b4a832ff` | GET /petclinic/api/pettypes/{n}/{n} (fora da especificação) | http_5xx | re1, re2, re3 | sim | `GET /petclinic/api/pettypes/160/160` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/160/160","status":500,"title":"NoResourceFoundExcepti` |
| `26f1bad69bf1` | GET /petclinic/api/specialties/{n}/{n} (fora da especificação) | http_5xx | re1, re2, re3 | sim | `GET /petclinic/api/specialties/174/174` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/174/174","status":500,"title":"NoResourceFoundExce` |
| `bc0035cf1f98` | GET /petclinic/api/vets/{n}/{n} (fora da especificação) | http_5xx | re1, re2, re3 | sim | `GET /petclinic/api/vets/571/571` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/571/571","status":500,"title":"NoResourceFoundException",` |
| `9b396577e81d` | PUT /api/owners/{ownerId} | http_5xx | re1, re2, re3 | sim | `PUT /petclinic/api/owners/239/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/239/","status":500,"title":"NoResourceFoundException","` |
| `25de0be4e0f8` | PUT /api/owners/{ownerId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | sim | `PUT /petclinic/api/owners/239/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/239/","status":500,"title":"NoResourceFoundException","` |
| `c8d3bb88edee` | PUT /api/pets | http_5xx | re1, re2, re3 | sim | `PUT /petclinic/api/pets/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/","status":500,"title":"NoResourceFoundException","type":` |
| `ef81f01d8b76` | PUT /api/pets | restler:InvalidValueChecker | re1, re2, re3 | sim | `PUT /petclinic/api/pets/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/","status":500,"title":"NoResourceFoundException","type":` |
| `f8c44335497a` | PUT /api/pettypes/{petTypeId} | http_5xx | re1, re2, re3 | sim | `PUT /petclinic/api/pettypes/164/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/164/","status":500,"title":"NoResourceFoundException"` |
| `7b353de85194` | PUT /api/pettypes/{petTypeId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | sim | `PUT /petclinic/api/pettypes/164/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/164/","status":500,"title":"NoResourceFoundException"` |
| `5bc7bc0a53bb` | PUT /api/specialties/{specialtyId} | http_5xx | re1, re2, re3 | sim | `PUT /petclinic/api/specialties/178/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/178/","status":500,"title":"NoResourceFoundExcepti` |
| `6b590cf39700` | PUT /api/specialties/{specialtyId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | sim | `PUT /petclinic/api/specialties/178/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/178/","status":500,"title":"NoResourceFoundExcepti` |
| `2453161a1321` | PUT /api/vets/{vetId} | http_5xx | re1, re2, re3 | sim | `PUT /petclinic/api/vets/567/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/567/","status":500,"title":"NoResourceFoundException","ty` |
| `21622f8ae645` | PUT /api/vets/{vetId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | sim | `PUT /petclinic/api/vets/567/?/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/567/","status":500,"title":"NoResourceFoundException","ty` |
| `3a82c03c428c` | PUT /petclinic/api/owners/{n}/{n} (fora da especificação) | http_5xx | re1, re2, re3 | sim | `PUT /petclinic/api/owners/239/239` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/239/239","status":500,"title":"NoResourceFoundException` |
| `c6173d075c9b` | PUT /petclinic/api/pets/{n}/w0AH( (fora da especificação) | http_5xx | re2 | sim | `PUT /petclinic/api/pets/62/w0AH(` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/62/w0AH(","status":500,"title":"NoResourceFoundException"` |
| `df0c9321b001` | PUT /petclinic/api/pettypes/{n}/{n} (fora da especificação) | http_5xx | re1, re2, re3 | sim | `PUT /petclinic/api/pettypes/164/164` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/164/164","status":500,"title":"NoResourceFoundExcepti` |
| `5019c1ed451a` | PUT /petclinic/api/specialties/{n}/{n} (fora da especificação) | http_5xx | re1, re2, re3 | sim | `PUT /petclinic/api/specialties/178/178` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/178/178","status":500,"title":"NoResourceFoundExce` |
| `8742f64c7603` | PUT /petclinic/api/vets/{n}/{n} (fora da especificação) | http_5xx | re1, re2, re3 | sim | `PUT /petclinic/api/vets/567/567` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/567/567","status":500,"title":"NoResourceFoundException",` |

Justificativa: 500: Caminho inexistente (ex.: /api/owners/320/?/ ou /api/owners/1/1) devolve 500 (NoResourceFoundException) em vez de 404: o tratador genérico de exceções transforma tudo em 500


### NOVO-petclinic-rest-2 — VP sugerido (26 relatos)

Parâmetro de caminho ou de consulta com tipo inválido (ex.: petId="abc", page="x") devolve 500 (MethodArgumentTypeMismatchException) em vez de 400.

Ferramentas: restler (6), schemathesis (24).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `faf4a040565a` | DELETE /api/owners/{ownerId} | http_5xx | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/owners/9.291458760714673e-162` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/9.291458760714673e-162","status":500,"title":"MethodArg` |
| `0dc6893da9f2` | DELETE /api/pets/{petId} | http_5xx | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/pets/3c%F0%B2%A3%AE%F1%AA%A0%BD%F2%91%AE%89_%3C%C2%8E%C3%88%C3%A1%C3%97%C2%ADG` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/3c%F0%B2%A3%AE%F1%AA%A0%BD%F2%91%AE%89_%3C%C2%8E%C3%88%C3` |
| `e5b9f6314b38` | DELETE /api/pettypes/{petTypeId} | http_5xx | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/pettypes/176046603317602816` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/176046603317602816","status":500,"title":"MethodArgum` |
| `d0293e0d66f1` | DELETE /api/specialties/{specialtyId} | http_5xx | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/specialties/J%C2%8F` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/J%C2%8F","status":500,"title":"MethodArgumentTypeM` |
| `875a16de8362` | DELETE /api/vets/{vetId} | http_5xx | sc1, sc2 | sim | `DELETE /petclinic/api/vets/-1757686955940` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/-1757686955940","status":500,"title":"MethodArgumentTypeM` |
| `2e412031d054` | DELETE /api/visits/{visitId} | http_5xx | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/visits/7732545515` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/visits/7732545515","status":500,"title":"MethodArgumentTypeMis` |
| `3ed8c49d431f` | GET /api/owners/{ownerId} | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/owners/2147483648` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/2147483648","status":500,"title":"MethodArgumentTypeMis` |
| `7449934893c2` | GET /api/owners/{ownerId}/pets/{petId} | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/owners/11/pets/2147483648` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/11/pets/2147483648","status":500,"title":"MethodArgumen` |
| `17ee46874a53` | GET /api/pets/{petId} | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `GET /petclinic/api/pets/petid47cf9a1c56` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/petid47cf9a1c56","status":500,"title":"MethodArgumentType` |
| `9277804d4dd1` | GET /api/pets/{petId} | restler:LeakageRuleChecker | re1, re2, re3 | sim | `GET /petclinic/api/pets/petid47cf9a1c56` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/petid47cf9a1c56","status":500,"title":"MethodArgumentType` |
| `4f3b31d46a81` | GET /api/pettypes/{petTypeId} | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/pettypes/2147483648` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/2147483648","status":500,"title":"MethodArgumentTypeM` |
| `8e592211829c` | GET /api/specialties/{specialtyId} | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/specialties/2147483648` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/2147483648","status":500,"title":"MethodArgumentTy` |
| `e0ef099d869e` | GET /api/v2/owners | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `GET /petclinic/api/v2/owners?lastName=fuzzstring&page=c&size=1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/v2/owners","status":500,"title":"MethodArgumentTypeMismatchExc` |
| `3fd694b67db5` | GET /api/v2/pets | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `GET /petclinic/api/v2/pets?page=c&size=1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/v2/pets","status":500,"title":"MethodArgumentTypeMismatchExcep` |
| `8f5c7ddf5092` | GET /api/vets/{vetId} | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/vets/2147483648` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/2147483648","status":500,"title":"MethodArgumentTypeMisma` |
| `cac71556e2b8` | GET /api/visits/{visitId} | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/visits/2147483648` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/visits/2147483648","status":500,"title":"MethodArgumentTypeMis` |
| `2d6c5960b9bb` | POST /api/owners/{ownerId}/pets | http_5xx | sc1, sc2, sc3 | sim | `POST /petclinic/api/owners/false/pets` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/false/pets","status":500,"title":"MethodArgumentTypeMis` |
| `1d2ed98cb113` | POST /api/owners/{ownerId}/pets/{petId}/visits | http_5xx | sc1, sc2, sc3 | sim | `POST /petclinic/api/owners/null/pets/34638224457587849620813803604148224/visits` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/null/pets/34638224457587849620813803604148224/visits","` |
| `0df89a81e9fc` | PUT /api/owners/{ownerId} | http_5xx | sc1, sc2, sc3 | sim | `PUT /petclinic/api/owners/%F0%9A%91%97` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/%F0%9A%91%97","status":500,"title":"MethodArgumentTypeM` |
| `4e457425871c` | PUT /api/owners/{ownerId}/pets/{petId} | http_5xx | sc1, sc2, sc3 | sim | `PUT /petclinic/api/owners/2147483647/pets/24006093804` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/2147483647/pets/24006093804","status":500,"title":"Meth` |
| `dc2b0b88935c` | PUT /api/pets/{petId} | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `PUT /petclinic/api/pets/petid9d56e15f95` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/petid9d56e15f95","status":500,"title":"MethodArgumentType` |
| `1ac8144d11da` | PUT /api/pets/{petId} | restler:PayloadBodyChecker | re1, re2, re3 | sim | `PUT /petclinic/api/pets/petidbb5fd432c2` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/petidbb5fd432c2","status":500,"title":"MethodArgumentType` |
| `35dbf73791b4` | PUT /api/pettypes/{petTypeId} | http_5xx | sc1, sc3 | sim | `PUT /petclinic/api/pettypes/35146.0` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/35146.0","status":500,"title":"MethodArgumentTypeMism` |
| `1546b3fe6d2e` | PUT /api/specialties/{specialtyId} | http_5xx | sc1, sc3 | sim | `PUT /petclinic/api/specialties/%F1%81%85%9Be` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/%F1%81%85%9Be","status":500,"title":"MethodArgumen` |
| `a3fd4969327f` | PUT /api/vets/{vetId} | http_5xx | sc1, sc2, sc3 | sim | `PUT /petclinic/api/vets/2750982679157` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/2750982679157","status":500,"title":"MethodArgumentTypeMi` |
| `12bb8614e35a` | PUT /api/visits/{visitId} | http_5xx | sc2, sc3 | sim | `PUT /petclinic/api/visits/19251515378` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/visits/19251515378","status":500,"title":"MethodArgumentTypeMi` |

Justificativa: 500: Parâmetro de caminho ou de consulta com tipo inválido (ex.: petId="abc", page="x") devolve 500 (MethodArgumentTypeMismatchException) em vez de 400


### NOVO-petclinic-rest-3 — VP sugerido (27 relatos)

Parâmetro que viola restrição de validação (ex.: id negativo, page/size < mínimo) devolve 500 (ConstraintViolationException) em vez de 400.

Ferramentas: evomaster (2), restler (7), schemathesis (24).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `f759c8534e4a` | DELETE /api/owners/{ownerId} | http_5xx | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/owners/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/-1","status":500,"title":"ConstraintViolationException"` |
| `e87c8f212c30` | DELETE /api/pets/{petId} | http_5xx | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/pets/-14953` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/-14953","status":500,"title":"ConstraintViolationExceptio` |
| `f713cc8dd241` | DELETE /api/pettypes/{petTypeId} | http_5xx | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/pettypes/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/-1","status":500,"title":"ConstraintViolationExceptio` |
| `6f7b4e20c709` | DELETE /api/specialties/{specialtyId} | http_5xx | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/specialties/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/-1","status":500,"title":"ConstraintViolationExcep` |
| `8ee7b6b0962f` | DELETE /api/vets/{vetId} | http_5xx | sc1, sc3 | sim | `DELETE /petclinic/api/vets/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/-1","status":500,"title":"ConstraintViolationException","` |
| `c8589794bd4a` | DELETE /api/visits/{visitId} | http_5xx | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/visits/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/visits/-1","status":500,"title":"ConstraintViolationException"` |
| `7e0d8cc91e31` | GET /api/owners/{ownerId} | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/owners/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/-1","status":500,"title":"ConstraintViolationException"` |
| `1931c78177ca` | GET /api/owners/{ownerId}/pets/{petId} | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/owners/-1/pets/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/-1/pets/-1","status":500,"title":"ConstraintViolationEx` |
| `1b8c030c7d33` | GET /api/pets/{petId} | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/pets/-797` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/-797","status":500,"title":"ConstraintViolationException"` |
| `b8dffe72c358` | GET /api/pettypes/{petTypeId} | http_5xx | sc1, sc3 | sim | `GET /petclinic/api/pettypes/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/-1","status":500,"title":"ConstraintViolationExceptio` |
| `86a0598c493a` | GET /api/specialties/{specialtyId} | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/specialties/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/-1","status":500,"title":"ConstraintViolationExcep` |
| `a3408d9ae19e` | GET /api/v2/owners | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `GET /petclinic/api/v2/owners?lastName=fuzzstring&page=-10&size=1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/v2/owners","status":500,"title":"ConstraintViolationException"` |
| `56ff733da0c2` | GET /api/v2/owners | restler:InvalidValueChecker | re1, re2, re3 | sim | `GET /petclinic/api/v2/owners?lastName=fuzzstring&page=-10&size=1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/v2/owners","status":500,"title":"ConstraintViolationException"` |
| `e04f7071193c` | GET /api/v2/pets | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `GET /petclinic/api/v2/pets?page=-10&size=1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/v2/pets","status":500,"title":"ConstraintViolationException","` |
| `736120fb4b1c` | GET /api/v2/pets | restler:InvalidValueChecker | re1, re2, re3 | sim | `GET /petclinic/api/v2/pets?page=-10&size=1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/v2/pets","status":500,"title":"ConstraintViolationException","` |
| `b2bf1874a106` | GET /api/visits/{visitId} | http_5xx | sc3 | sim | `GET /petclinic/api/visits/-1028` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/visits/-1028","status":500,"title":"ConstraintViolationExcepti` |
| `1bccf7eab85e` | POST /api/owners | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc1, sc2, sc3 | sim | `POST /petclinic/api/owners` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners","status":500,"title":"ConstraintViolationException","t` |
| `8e534942bdf5` | POST /api/owners/{ownerId}/pets | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc1, sc2, sc3 | sim | `POST /petclinic/api/owners/743/pets` → 404 |
| `225e257535c3` | POST /api/owners/{ownerId}/pets | restler:InvalidValueChecker | re1, re2, re3 | não | `POST /petclinic/api/owners/544/pets` → 404 |
| `3be304647855` | POST /api/owners/{ownerId}/pets/{petId}/visits | http_5xx | sc1, sc2, sc3 | sim | `POST /petclinic/api/owners/-1/pets/-1/visits` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/-1/pets/-1/visits","status":500,"title":"ConstraintViol` |
| `4731fa87416b` | PUT /api/owners/{ownerId} | http_5xx | sc1, sc2, sc3 | sim | `PUT /petclinic/api/owners/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/-1","status":500,"title":"ConstraintViolationException"` |
| `61697d40fcbc` | PUT /api/owners/{ownerId}/pets/{petId} | http_5xx | sc1, sc2, sc3 | sim | `PUT /petclinic/api/owners/0/pets/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/0/pets/-1","status":500,"title":"ConstraintViolationExc` |
| `410f03cd1515` | PUT /api/pets/{petId} | http_5xx | sc1, sc2, sc3 | sim | `PUT /petclinic/api/pets/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/-1","status":500,"title":"ConstraintViolationException","` |
| `3f2e28c0f76f` | PUT /api/pettypes/{petTypeId} | http_5xx | sc1, sc2, sc3 | sim | `PUT /petclinic/api/pettypes/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/-1","status":500,"title":"ConstraintViolationExceptio` |
| `31da23b044e2` | PUT /api/specialties/{specialtyId} | http_5xx | sc1, sc2, sc3 | sim | `PUT /petclinic/api/specialties/-1547420` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/-1547420","status":500,"title":"ConstraintViolatio` |
| `274831f0d584` | PUT /api/vets/{vetId} | http_5xx | sc1, sc2, sc3 | sim | `PUT /petclinic/api/vets/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/-1","status":500,"title":"ConstraintViolationException","` |
| `c5faf3f21c9f` | PUT /api/visits/{visitId} | http_5xx | sc2, sc3 | sim | `PUT /petclinic/api/visits/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/visits/-1","status":500,"title":"ConstraintViolationException"` |

Justificativa: 500: Parâmetro que viola restrição de validação (ex.: id negativo, page/size < mínimo) devolve 500 (ConstraintViolationException) em vez de 400


### NOVO-petclinic-rest-4 — VP sugerido (35 relatos)

Corpo JSON malformado ou com tipo errado devolve 500 (HttpMessageNotReadableException) em vez de 400.

Ferramentas: evomaster (6), restler (31), schemathesis (15).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `e6d9edc1043b` | POST /api/owners | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `POST /petclinic/api/owners` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners","status":500,"title":"HttpMessageNotReadableException"` |
| `69f79779f1d1` | POST /api/owners | restler:InvalidValueChecker | re1, re2, re3 | sim | `POST /petclinic/api/owners` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners","status":500,"title":"HttpMessageNotReadableException"` |
| `d0b63760cc06` | POST /api/owners | restler:PayloadBodyChecker | re1, re2, re3 | sim | `POST /petclinic/api/owners` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners","status":500,"title":"HttpMessageNotReadableException"` |
| `6b7ffc9df57c` | POST /api/owners/{ownerId}/pets | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc1, sc2, sc3 | sim | `POST /petclinic/api/owners/955/pets` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/955/pets","status":500,"title":"HttpMessageNotReadableE` |
| `48345ed6cfc7` | POST /api/owners/{ownerId}/pets | restler:PayloadBodyChecker | re1, re2, re3 | sim | `POST /petclinic/api/owners/482/pets` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/482/pets","status":500,"title":"HttpMessageNotReadableE` |
| `f0324758d7b1` | POST /api/owners/{ownerId}/pets/{petId}/visits | http_5xx | ev1, ev2, ev3, sc1, sc2, sc3 | sim | `POST /petclinic/api/owners/320/pets/512/visits` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/320/pets/512/visits","status":500,"title":"HttpMessageN` |
| `42f526969d77` | POST /api/pettypes | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `POST /petclinic/api/pettypes` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes","status":500,"title":"HttpMessageNotReadableExceptio` |
| `79c7960962e7` | POST /api/pettypes | restler:InvalidValueChecker | re1, re2, re3 | sim | `POST /petclinic/api/pettypes` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes","status":500,"title":"HttpMessageNotReadableExceptio` |
| `4546403afd90` | POST /api/pettypes | restler:PayloadBodyChecker | re1, re2, re3 | sim | `POST /petclinic/api/pettypes` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes","status":500,"title":"HttpMessageNotReadableExceptio` |
| `357b822e81f9` | POST /api/specialties | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `POST /petclinic/api/specialties` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties","status":500,"title":"HttpMessageNotReadableExcep` |
| `9a7fa2370e82` | POST /api/specialties | restler:InvalidValueChecker | re1, re2, re3 | sim | `POST /petclinic/api/specialties` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties","status":500,"title":"HttpMessageNotReadableExcep` |
| `1ffc2dad3eb5` | POST /api/users | http_5xx | re1, re2, re3, sc3 | sim | `POST /petclinic/api/users` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/users","status":500,"title":"HttpMessageNotReadableException",` |
| `4c9d4c849fd7` | POST /api/users | restler:InvalidValueChecker | re1, re2, re3 | sim | `POST /petclinic/api/users` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/users","status":500,"title":"HttpMessageNotReadableException",` |
| `f1e3c550bf9b` | POST /api/users | restler:PayloadBodyChecker | re1, re2, re3 | sim | `POST /petclinic/api/users` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/users","status":500,"title":"HttpMessageNotReadableException",` |
| `8737c8bde30a` | POST /api/vets | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `POST /petclinic/api/vets` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets","status":500,"title":"HttpMessageNotReadableException","` |
| `720722bac76c` | POST /api/vets | restler:InvalidValueChecker | re1, re2, re3 | sim | `POST /petclinic/api/vets` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets","status":500,"title":"HttpMessageNotReadableException","` |
| `b7c1a7bb6f0c` | POST /api/vets | restler:PayloadBodyChecker | re1, re2, re3 | sim | `POST /petclinic/api/vets` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets","status":500,"title":"HttpMessageNotReadableException","` |
| `7d3139ca7573` | POST /api/visits | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc1, sc2, sc3 | sim | `POST /petclinic/api/visits` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/visits","status":500,"title":"HttpMessageNotReadableException"` |
| `c4af1c619be8` | POST /api/visits | restler:InvalidValueChecker | re1, re2, re3 | sim | `POST /petclinic/api/visits` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/visits","status":500,"title":"HttpMessageNotReadableException"` |
| `1a7fa6991797` | POST /api/visits | restler:PayloadBodyChecker | re1, re2, re3 | sim | `POST /petclinic/api/visits` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/visits","status":500,"title":"HttpMessageNotReadableException"` |
| `757fc3a99e2c` | PUT /api/owners/{ownerId} | http_5xx | re1, re2, re3, sc1, sc3 | sim | `PUT /petclinic/api/owners/241` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/241","status":500,"title":"HttpMessageNotReadableExcept` |
| `0d4d46aaf41b` | PUT /api/owners/{ownerId} | restler:InvalidValueChecker | re1, re2, re3 | sim | `PUT /petclinic/api/owners/298` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/298","status":500,"title":"HttpMessageNotReadableExcept` |
| `273273fb90d3` | PUT /api/owners/{ownerId} | restler:PayloadBodyChecker | re1, re2, re3 | sim | `PUT /petclinic/api/owners/244` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/244","status":500,"title":"HttpMessageNotReadableExcept` |
| `f1537a482f12` | PUT /api/owners/{ownerId}/pets/{petId} | http_5xx | ev1, ev2, ev3, sc1, sc2, sc3 | sim | `PUT /petclinic/api/owners/620/pets/106` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/620/pets/106","status":500,"title":"HttpMessageNotReada` |
| `173e02c37f82` | PUT /api/pets/{petId} | http_5xx | ev1, ev2, ev3, sc1, sc2, sc3 | sim | `PUT /petclinic/api/pets/612` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/612","status":500,"title":"HttpMessageNotReadableExceptio` |
| `cb1edcd8dbf7` | PUT /api/pettypes/{petTypeId} | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `PUT /petclinic/api/pettypes/167` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/167","status":500,"title":"HttpMessageNotReadableExce` |
| `25009400b62d` | PUT /api/pettypes/{petTypeId} | restler:InvalidValueChecker | re1, re2, re3 | sim | `PUT /petclinic/api/pettypes/205` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/205","status":500,"title":"HttpMessageNotReadableExce` |
| `ff40f914e7b0` | PUT /api/pettypes/{petTypeId} | restler:PayloadBodyChecker | re1, re2, re3 | sim | `PUT /petclinic/api/pettypes/167` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/167","status":500,"title":"HttpMessageNotReadableExce` |
| `b5c64daa72de` | PUT /api/specialties/{specialtyId} | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `PUT /petclinic/api/specialties/181` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/181","status":500,"title":"HttpMessageNotReadableE` |
| `f2cd8889ce50` | PUT /api/specialties/{specialtyId} | restler:InvalidValueChecker | re1, re2, re3 | sim | `PUT /petclinic/api/specialties/218` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/218","status":500,"title":"HttpMessageNotReadableE` |
| `61ced1f3d41d` | PUT /api/specialties/{specialtyId} | restler:PayloadBodyChecker | re1, re2, re3 | sim | `PUT /petclinic/api/specialties/187` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/187","status":500,"title":"HttpMessageNotReadableE` |
| `52996fa4f9ec` | PUT /api/vets/{vetId} | http_5xx | re1, re2, re3, sc1, sc2, sc3 | sim | `PUT /petclinic/api/vets/1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/1","status":500,"title":"HttpMessageNotReadableException"` |
| `7ed0a1fcf99f` | PUT /api/vets/{vetId} | restler:InvalidValueChecker | re1, re2, re3 | sim | `PUT /petclinic/api/vets/1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/1","status":500,"title":"HttpMessageNotReadableException"` |
| `8b17a6963a78` | PUT /api/vets/{vetId} | restler:PayloadBodyChecker | re1, re2, re3 | sim | `PUT /petclinic/api/vets/1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/1","status":500,"title":"HttpMessageNotReadableException"` |
| `177ab76902b2` | PUT /api/visits/{visitId} | http_5xx | ev1, ev2, ev3, sc1, sc2, sc3 | sim | `PUT /petclinic/api/visits/427` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/visits/427","status":500,"title":"HttpMessageNotReadableExcept` |

Justificativa: 500: Corpo JSON malformado ou com tipo errado devolve 500 (HttpMessageNotReadableException) em vez de 400


### NOVO-petclinic-rest-5 — VP sugerido (10 relatos)

Requisição com Content-Type multipart/form-data sem boundary devolve 500 (MultipartException) em vez de 400/415.

Ferramentas: schemathesis (10).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `36d1406e45ed` | GET /api/owners | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/owners?lastName=Franklin` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners","status":500,"title":"MultipartException","type":"http` |
| `6c219d71deed` | GET /api/owners | schemathesis:ST102 | sc1, sc2, sc3 | sim | `GET /petclinic/api/owners?lastName=Franklin` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners","status":500,"title":"MultipartException","type":"http` ferramenta: - ST102 Server error on undeclared request Content-Type |
| `18080648cc7c` | GET /api/pettypes | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/pettypes` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes","status":500,"title":"MultipartException","type":"ht` |
| `c13790b5296b` | GET /api/pettypes | schemathesis:ST102 | sc1, sc2, sc3 | sim | `GET /petclinic/api/pettypes` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes","status":500,"title":"MultipartException","type":"ht` ferramenta: - ST102 Server error on undeclared request Content-Type |
| `ed3cbaab65c0` | GET /api/specialties | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/specialties` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties","status":500,"title":"MultipartException","type":` |
| `6bbb0c8526ec` | GET /api/specialties | schemathesis:ST102 | sc1, sc2, sc3 | sim | `GET /petclinic/api/specialties` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties","status":500,"title":"MultipartException","type":` ferramenta: - ST102 Server error on undeclared request Content-Type |
| `4cd72838e945` | GET /api/vets | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/vets` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets","status":500,"title":"MultipartException","type":"http:/` |
| `90927c82762a` | GET /api/vets | schemathesis:ST102 | sc1, sc2, sc3 | sim | `GET /petclinic/api/vets` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets","status":500,"title":"MultipartException","type":"http:/` ferramenta: - ST102 Server error on undeclared request Content-Type |
| `7c1fcba67de5` | OPTIONS / | http_5xx | sc1, sc2, sc3 | sim | `OPTIONS /petclinic/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/","status":500,"title":"MultipartException","type":"http://api:808` |
| `f28041f6569f` | OPTIONS / | schemathesis:ST102 | sc1, sc2, sc3 | sim | `OPTIONS /petclinic/` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/","status":500,"title":"MultipartException","type":"http://api:808` ferramenta: - ST102 Server error on undeclared request Content-Type |

Justificativa: 500: Requisição com Content-Type multipart/form-data sem boundary devolve 500 (MultipartException) em vez de 400/415


### NOVO-petclinic-rest-6 — VP sugerido (4 relatos)

Content-Type não suportado no corpo devolve 500 (HttpMediaTypeNotSupportedException) em vez de 415.

Ferramentas: schemathesis (4).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `bc19c800999a` | POST /api/owners | http_5xx | sc1, sc2, sc3 | sim | `POST /petclinic/api/owners` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners","status":500,"title":"HttpMediaTypeNotSupportedExcepti` |
| `a405076744b8` | POST /api/owners/{ownerId}/pets | http_5xx | sc1, sc2, sc3 | sim | `POST /petclinic/api/owners/11/pets` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/11/pets","status":500,"title":"HttpMediaTypeNotSupporte` |
| `447e6b31d5c5` | POST /api/owners/{ownerId}/pets/{petId}/visits | http_5xx | sc1, sc2, sc3 | sim | `POST /petclinic/api/owners/1/pets/15/visits` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/1/pets/15/visits","status":500,"title":"HttpMediaTypeNo` |
| `de6bad5a479c` | PUT /api/owners/{ownerId}/pets/{petId} | http_5xx | sc1, sc2, sc3 | sim | `PUT /petclinic/api/owners/11/pets/16` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/11/pets/16","status":500,"title":"HttpMediaTypeNotSuppo` |

Justificativa: 500: Content-Type não suportado no corpo devolve 500 (HttpMediaTypeNotSupportedException) em vez de 415


### NOVO-petclinic-rest-7 — VP sugerido (3 relatos)

Parâmetro de consulta sem nome (ex.: ?=false) devolve 500 (InvalidParameterException) em vez de 400.

Ferramentas: schemathesis (3).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `eb7221d1e2f2` | GET /api/owners | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/owners?lastName=%C3%89&=false` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners","status":500,"title":"InvalidParameterException","type` |
| `420982a861ac` | GET /api/v2/owners | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/v2/owners?=&size=87&lastName=&page=136021&l-%C3%BE%C3%B4=false&l-%C3%BE%C3%B4=%F2%A9%81%97&l-%C3%BE%C3%B4=%7CX` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/v2/owners","status":500,"title":"InvalidParameterException","t` |
| `22f93a57d6c7` | GET /api/v2/pets | http_5xx | sc1, sc2, sc3 | sim | `GET /petclinic/api/v2/pets?=false` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/v2/pets","status":500,"title":"InvalidParameterException","typ` |

Justificativa: 500: Parâmetro de consulta sem nome (ex.: ?=false) devolve 500 (InvalidParameterException) em vez de 400


### NOVO-petclinic-rest-8 — VP sugerido (4 relatos)

POST de specialty/vet/visit com "id" de entidade inexistente no corpo devolve 500 (ObjectOptimisticLockingFailureException em ClinicServiceImpl.saveSpecialty/saveVet/saveVisit).

Ferramentas: evomaster (3), restler (3), schemathesis (2).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `e41e982f04a8` | POST /api/specialties | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc2 | sim | `POST /petclinic/api/specialties` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties","status":500,"title":"ObjectOptimisticLockingFail` |
| `d556219276b7` | POST /api/specialties | restler:PayloadBodyChecker | re1, re2, re3 | sim | `POST /petclinic/api/specialties` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties","status":500,"title":"ObjectOptimisticLockingFail` |
| `7633f08e38a0` | POST /api/vets | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc3 | sim | `POST /petclinic/api/vets` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets","status":500,"title":"ObjectOptimisticLockingFailureExce` |
| `e97d864c94b4` | POST /api/visits | http_5xx | ev1, ev2, ev3 | sim | `POST /petclinic/api/visits` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/visits","status":500,"title":"ObjectOptimisticLockingFailureEx` |

Justificativa: 500: POST de specialty/vet/visit com "id" de entidade inexistente no corpo devolve 500 (ObjectOptimisticLockingFailureException em ClinicServiceImpl.saveSpecialty/saveVet/saveVisit)


### NOVO-petclinic-rest-9 — VP sugerido (2 relatos)

GET /api/v2/owners e /api/v2/pets com page*size acima de Integer.MAX_VALUE devolvem 500 (InvalidDataAccessApiUsageException: page offset exceeds Integer.MAX_VALUE).

Ferramentas: evomaster (2), schemathesis (2).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `8fe2f7f1c391` | GET /api/v2/owners | http_5xx | ev1, ev2, ev3, sc1, sc2, sc3 | sim | `GET /petclinic/api/v2/owners?lastName=Escobito&page=1536041074` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/v2/owners","status":500,"title":"InvalidDataAccessApiUsageExce` |
| `fc308cfd5a90` | GET /api/v2/pets | http_5xx | ev1, ev2, ev3, sc1, sc2, sc3 | sim | `GET /petclinic/api/v2/pets?page=1306141009` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/v2/pets","status":500,"title":"InvalidDataAccessApiUsageExcept` |

Justificativa: 500: GET /api/v2/owners e /api/v2/pets com page*size acima de Integer.MAX_VALUE devolvem 500 (InvalidDataAccessApiUsageException: page offset exceeds Integer.MAX_VALUE)


### NOVO-petclinic-rest-10 — VP sugerido (2 relatos)

PUT de owner/pet com campos que violam as validações da entidade só falha no commit: 500 (TransactionSystemException) em vez de 400.

Ferramentas: evomaster (1), restler (1), schemathesis (2).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `acdcbb1d02f4` | PUT /api/owners/{ownerId} | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc1, sc2, sc3 | sim | `PUT /petclinic/api/owners/34` → 404 |
| `8a9977537d56` | PUT /api/pets/{petId} | http_5xx | sc1, sc3 | sim | `PUT /petclinic/api/pets/23` → 404 |

Justificativa: 500: PUT de owner/pet com campos que violam as validações da entidade só falha no commit: 500 (TransactionSystemException) em vez de 400. Reproduzido à mão (data/processed/reproducao/manual_*.txt)


### NOVO-petclinic-rest-11 — VP sugerido (1 relato)

POST /api/users sem papéis (roles) devolve 500 (IllegalArgumentException "User must have at least a role set!" em UserServiceImpl.saveUser) em vez de 400.

Ferramentas: evomaster (1), restler (1), schemathesis (1).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `f05be19f48b6` | POST /api/users | http_5xx | ev1, ev2, ev3, re1, re2, re3, sc1, sc2, sc3 | sim | `POST /petclinic/api/users` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/users","status":500,"title":"IllegalArgumentException","type":` |

Justificativa: 500: POST /api/users sem papéis (roles) devolve 500 (IllegalArgumentException "User must have at least a role set!" em UserServiceImpl.saveUser) em vez de 400


### NOVO-petclinic-rest-12 — VP sugerido (1 relato)

POST /api/users com papel sem nome: NullPointerException em UserServiceImpl.saveUser (Role.getName), 500.

Ferramentas: schemathesis (1).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `92164e480f1f` | POST /api/users | http_5xx | sc3 | sim | `POST /petclinic/api/users` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/users","status":500,"title":"NullPointerException","type":"htt` |

Justificativa: 500: POST /api/users com papel sem nome: NullPointerException em UserServiceImpl.saveUser (Role.getName), 500


### NOVO-petclinic-rest-13 — VP sugerido (1 relato)

POST /api/visits com petId inexistente devolve 500 (ObjectRetrievalFailureException) em vez de 404/400.

Ferramentas: evomaster (1).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `34b6776b8919` | POST /api/visits | http_5xx | ev1, ev2, ev3 | sim | `POST /petclinic/api/visits` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/visits","status":500,"title":"ObjectRetrievalFailureException"` |

Justificativa: 500: POST /api/visits com petId inexistente devolve 500 (ObjectRetrievalFailureException) em vez de 404/400


### FP sugerido (4 relatos)

Causa: API rejeita com 400 uma entrada que a especificação não restringe (especificação incompleta); 400 é a resposta correta.

Ferramentas: schemathesis (4).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `1d857193bbc2` | POST /api/owners/{ownerId}/pets | schemathesis:ST202 | sc1, sc2 | sim | `POST /petclinic/api/owners/12/pets` → 400 `{"detail":"The request contains invalid or missing parameters","instance":"/petclinic/api/owners/12/pets","status":400,"title":"MethodArgumentNotValidException"` ferramenta: - ST202 Schema-valid request rejected |
| `6901dbf723a4` | PUT /api/owners/{ownerId}/pets/{petId} | schemathesis:ST202 | sc3 | sim | `PUT /petclinic/api/owners/1/pets/15` → 400 `{"detail":"The request contains invalid or missing parameters","instance":"/petclinic/api/owners/1/pets/15","status":400,"title":"MethodArgumentNotValidExceptio` ferramenta: - ST202 Schema-valid request rejected |
| `4d9cb229eaab` | PUT /api/pets/{petId} | schemathesis:ST202 | sc1, sc3 | sim | `PUT /petclinic/api/pets/16` → 400 `{"detail":"The request contains invalid or missing parameters","instance":"/petclinic/api/pets/16","status":400,"title":"MethodArgumentNotValidException","type"` ferramenta: - ST202 Schema-valid request rejected |
| `025693be262d` | Stateful tests | schemathesis:ST202 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/owners/839775/pets/41` → 400 `{"detail":"The request contains invalid or missing parameters","instance":"/petclinic/api/owners/839775/pets/41","status":400,"title":"MethodArgumentNotValidExc` ferramenta: - ST202 Schema-valid request rejected |

### FP sugerido (3 relatos)

Causa: API tolerante: aceita entrada fora do schema e responde normalmente, sem falha.

Ferramentas: schemathesis (3).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `22da7be95301` | PUT /api/pettypes/{petTypeId} | schemathesis:ST201 | sc1, sc2, sc3 | não | `PUT /petclinic/api/pettypes/897` → 404 ferramenta: - ST201 Schema-violating request accepted |
| `7c90a303bcec` | PUT /api/specialties/{specialtyId} | schemathesis:ST201 | sc3 | não | `PUT /petclinic/api/specialties/1104` → 404 ferramenta: - ST201 Schema-violating request accepted |
| `7fd54e963362` | Stateful tests | schemathesis:ST201 | sc1, sc2, sc3 | sim | `POST /petclinic/api/specialties` → 201 `{"id":4,"name":"81"}` ferramenta: - ST201 Schema-violating request accepted |

### FP sugerido (30 relatos)

Causa: Content-Type da resposta diferente do documentado (padrão do framework); sem falha da API.

Ferramentas: schemathesis (30).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `358bd82558e8` | DELETE /api/owners/{ownerId} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/owners/1` → 204 ferramenta: - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `94560238ff04` | DELETE /api/pets/{petId} | schemathesis:ST105 | sc1, sc2 | sim | `DELETE /petclinic/api/pets/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/-1","status":500,"title":"ConstraintViolationException","` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `d3a868d6d8bf` | DELETE /api/pettypes/{petTypeId} | schemathesis:ST105 | sc3 | sim | `DELETE /petclinic/api/pettypes/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/-1","status":500,"title":"ConstraintViolationExceptio` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `0f2b47b3918c` | DELETE /api/vets/{vetId} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/vets/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/-1","status":500,"title":"ConstraintViolationException","` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `d151768ae557` | DELETE /api/visits/{visitId} | schemathesis:ST105 | sc2 | sim | `DELETE /petclinic/api/visits/-1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/visits/-1","status":500,"title":"ConstraintViolationException"` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `a6ee0f0265c0` | GET /api/owners/{ownerId} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `GET /petclinic/api/owners/2147483648` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/2147483648","status":500,"title":"MethodArgumentTypeMis` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `64ed8b17dd12` | GET /api/owners/{ownerId}/pets/{petId} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `GET /petclinic/api/owners/11/pets/2147483648` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/11/pets/2147483648","status":500,"title":"MethodArgumen` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `ba60b7e6cec6` | GET /api/pets/{petId} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `GET /petclinic/api/pets/2147483648` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/2147483648","status":500,"title":"MethodArgumentTypeMisma` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `b1c7d9cf7e4d` | GET /api/pettypes/{petTypeId} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `GET /petclinic/api/pettypes/2147483648` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/2147483648","status":500,"title":"MethodArgumentTypeM` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `2f8dd8792e46` | GET /api/specialties/{specialtyId} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `GET /petclinic/api/specialties/2147483648` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/2147483648","status":500,"title":"MethodArgumentTy` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `f2426faf4299` | GET /api/v2/owners | schemathesis:ST105 | sc1, sc2, sc3 | sim | `GET /petclinic/api/v2/owners?size=0` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/v2/owners","status":500,"title":"ConstraintViolationException"` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `cd507552a720` | GET /api/v2/pets | schemathesis:ST105 | sc1, sc2, sc3 | sim | `GET /petclinic/api/v2/pets?size=0` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/v2/pets","status":500,"title":"ConstraintViolationException","` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `c1e94ba6c34e` | GET /api/vets/{vetId} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `GET /petclinic/api/vets/2147483648` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/2147483648","status":500,"title":"MethodArgumentTypeMisma` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `dda3a6ade046` | GET /api/visits/{visitId} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `GET /petclinic/api/visits/2147483648` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/visits/2147483648","status":500,"title":"MethodArgumentTypeMis` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `a8d0c9818993` | POST /api/owners | schemathesis:ST105 | sc1, sc2, sc3 | sim | `POST /petclinic/api/owners` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners","status":500,"title":"HttpMediaTypeNotSupportedExcepti` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `2c5fda1c7ac9` | POST /api/owners/{ownerId}/pets | schemathesis:ST105 | sc1, sc2, sc3 | sim | `POST /petclinic/api/owners/11/pets` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/11/pets","status":500,"title":"HttpMediaTypeNotSupporte` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `cffed38b386e` | POST /api/owners/{ownerId}/pets/{petId}/visits | schemathesis:ST105 | sc1, sc2, sc3 | sim | `POST /petclinic/api/owners/1/pets/15/visits` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/1/pets/15/visits","status":500,"title":"HttpMediaTypeNo` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `acde563fbe43` | POST /api/pettypes | schemathesis:ST105 | sc1, sc2, sc3 | sim | `POST /petclinic/api/pettypes` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes","status":500,"title":"HttpMessageNotReadableExceptio` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `633e0df406df` | POST /api/specialties | schemathesis:ST105 | sc1, sc2, sc3 | sim | `POST /petclinic/api/specialties` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties","status":500,"title":"HttpMessageNotReadableExcep` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `e8310d731f09` | POST /api/users | schemathesis:ST105 | sc1, sc2, sc3 | sim | `POST /petclinic/api/users` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/users","status":500,"title":"IllegalArgumentException","type":` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `6bc04f4e7d14` | POST /api/vets | schemathesis:ST105 | sc1, sc2, sc3 | sim | `POST /petclinic/api/vets` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets","status":500,"title":"HttpMessageNotReadableException","` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `c4caa3394e82` | POST /api/visits | schemathesis:ST105 | sc1, sc2, sc3 | sim | `POST /petclinic/api/visits` → 404 `{"detail":"The requested resource could not be processed due to a data constraint violation","instance":"/petclinic/api/visits","status":404,"title":"DataIntegr` ferramenta: - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `e526039d3863` | PUT /api/owners/{ownerId} | schemathesis:ST105 | sc1, sc3 | sim | `PUT /petclinic/api/owners/11` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/11","status":500,"title":"HttpMessageNotReadableExcepti` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `ca0855ee0025` | PUT /api/owners/{ownerId}/pets/{petId} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/owners/11/pets/16` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/owners/11/pets/16","status":500,"title":"HttpMediaTypeNotSuppo` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `a288a3fe5824` | PUT /api/pets/{petId} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/pets/16` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pets/16","status":500,"title":"HttpMessageNotReadableException` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `92371f8806b4` | PUT /api/pettypes/{petTypeId} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/pettypes/7` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/pettypes/7","status":500,"title":"HttpMessageNotReadableExcept` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `5fff667ab74f` | PUT /api/specialties/{specialtyId} | schemathesis:ST105 | sc1, sc2 | sim | `PUT /petclinic/api/specialties/1` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/1","status":500,"title":"HttpMessageNotReadableExc` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `8e60a836b7ad` | PUT /api/vets/{vetId} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/vets/7` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/vets/7","status":500,"title":"HttpMessageNotReadableException"` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `2f3f4c621da4` | PUT /api/visits/{visitId} | schemathesis:ST105 | sc2, sc3 | sim | `PUT /petclinic/api/visits/58` → 404 ferramenta: - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `3bdfbb7951a0` | Stateful tests | schemathesis:ST105 | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/specialties/J%C2%8F` → 500 `{"detail":"An unexpected error occurred while processing your request","instance":"/petclinic/api/specialties/J%C2%8F","status":500,"title":"MethodArgumentTypeM` ferramenta: - ST101 Server error; - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |

### FP sugerido (8 relatos)

Causa: RESTler (InvalidDynamicObjectChecker, bucket 20x) anexou ?injected_query_string=123 ao caminho de um objeto válido e esperava erro; a API ignora o parâmetro desconhecido e devolve o objeto (20x), comportamento aceitável.

Ferramentas: restler (8).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `abd04047ac0b` | GET /api/owners/{ownerId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | não | `GET /petclinic/api/owners/235?injected_query_string=123` → 404 |
| `ac96d368540b` | GET /api/pettypes/{petTypeId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | não | `GET /petclinic/api/pettypes/160?injected_query_string=123` → 404 |
| `b7daeb61866e` | GET /api/specialties/{specialtyId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | não | `GET /petclinic/api/specialties/174?injected_query_string=123` → 404 |
| `b44d15bbaa67` | GET /api/vets/{vetId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | não | `GET /petclinic/api/vets/571?injected_query_string=123` → 404 |
| `93dc08e2e848` | PUT /api/owners/{ownerId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | não | `PUT /petclinic/api/owners/239?injected_query_string=123` → 404 |
| `42e5f1501ba5` | PUT /api/pettypes/{petTypeId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | não | `PUT /petclinic/api/pettypes/164?injected_query_string=123` → 404 |
| `8e47e5676085` | PUT /api/specialties/{specialtyId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | não | `PUT /petclinic/api/specialties/178?injected_query_string=123` → 404 |
| `55541040ef88` | PUT /api/vets/{vetId} | restler:InvalidDynamicObjectChecker | re1, re2, re3 | não | `PUT /petclinic/api/vets/567?injected_query_string=123` → 404 |

### FP sugerido (25 relatos)

Causa: código de status correto para a situação, mas não listado na especificação.

Ferramentas: schemathesis (25).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `f4302a33c6cd` | DELETE / | schemathesis:ST103 | sc1, sc2, sc3 | sim | `DELETE /petclinic/` → 302 ferramenta: - ST103 Undocumented status code; Received: 302; Documented: 200 |
| `1c7ebaa96790` | DELETE /api/owners/{ownerId} | schemathesis:ST103 | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/owners/7` → 204 ferramenta: - ST103 Undocumented status code; Received: 204; Documented: 200, 304, 400, 404, 500 |
| `f76572592397` | DELETE /api/pets/{petId} | schemathesis:ST103 | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/pets/1` → 204 ferramenta: - ST103 Undocumented status code; Received: 204; Documented: 200, 304, 400, 404, 500 |
| `9e5f5a6b84e7` | DELETE /api/pettypes/{petTypeId} | schemathesis:ST103 | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/pettypes/1` → 204 ferramenta: - ST103 Undocumented status code; Received: 204; Documented: 200, 304, 400, 404, 500 |
| `750416e89e89` | DELETE /api/specialties/{specialtyId} | schemathesis:ST103 | sc1, sc2, sc3 | não | `DELETE /petclinic/api/specialties/5` → 404 ferramenta: - ST103 Undocumented status code; Received: 204; Documented: 200, 304, 400, 404, 500 |
| `fc62030b5f24` | DELETE /api/vets/{vetId} | schemathesis:ST103 | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/vets/1` → 204 ferramenta: - ST103 Undocumented status code; Received: 204; Documented: 200, 304, 400, 404, 500 |
| `5d0ad452e3ef` | GET / | schemathesis:ST103 | sc1, sc2, sc3 | sim | `GET /petclinic/` → 302 ferramenta: - ST103 Undocumented status code; Received: 302; Documented: 200 |
| `97577333de5d` | GET /api/owners | schemathesis:ST103 | sc1, sc2, sc3 | não | `GET /petclinic/api/owners?lastName=Coleman` → 200 `[{"firstName":"Jean","lastName":"Coleman","address":"105 N. Lake St.","city":"Monona","telephone":"6085552654","pets":[{"name":"Max","birthDate":"2012-09-04","t` ferramenta: - ST103 Undocumented status code; Received: 404; Documented: 200, 304, 500 |
| `74b1a7802f8f` | GET /api/visits | schemathesis:ST103 | sc1, sc2, sc3 | não | `GET /petclinic/api/visits` → 200 `[{"description":"rabies shot","id":1,"petId":7,"date":"2013-01-01"},{"description":"rabies shot","id":2,"petId":8,"date":"2013-01-02"},{"description":"neutered"` ferramenta: - ST103 Undocumented status code; Received: 404; Documented: 200, 304, 500 |
| `2686921a03d8` | HEAD / | schemathesis:ST103 | sc1, sc2, sc3 | sim | `HEAD /petclinic/` → 302 ferramenta: - ST103 Undocumented status code; Received: 302; Documented: 200 |
| `0077df40312c` | PATCH / | schemathesis:ST103 | sc1, sc2, sc3 | sim | `PATCH /petclinic/` → 302 ferramenta: - ST103 Undocumented status code; Received: 302; Documented: 200 |
| `6031258cf8b1` | POST / | schemathesis:ST103 | sc1, sc2, sc3 | sim | `POST /petclinic/` → 302 ferramenta: - ST103 Undocumented status code; Received: 302; Documented: 200 |
| `780b48988449` | POST /api/pettypes | schemathesis:ST103 | sc1, sc2, sc3 | sim | `POST /petclinic/api/pettypes` → 201 `{"name":"cat","id":7}` ferramenta: - ST103 Undocumented status code; Received: 201; Documented: 200, 304, 400, 404, 500 |
| `7f65c7c1cacd` | POST /api/specialties | schemathesis:ST103 | sc1, sc2, sc3 | sim | `POST /petclinic/api/specialties` → 201 `{"id":4,"name":"radiology"}` ferramenta: - ST103 Undocumented status code; Received: 201; Documented: 200, 304, 400, 404, 500 |
| `8ea249300f82` | POST /api/users | schemathesis:ST103 | sc1, sc2, sc3 | sim | `POST /petclinic/api/users` → 201 `{"username":"john.doe","enabled":true,"password":"valorFiltrado1","roles":[{"name":"ROLE_admin"}]}` ferramenta: - ST103 Undocumented status code; Received: 201; Documented: 200, 304, 400, 404, 500 |
| `24fb1bff39a3` | POST /api/vets | schemathesis:ST103 | sc1, sc2, sc3 | sim | `POST /petclinic/api/vets` → 201 `{"firstName":"James","lastName":"Carter","specialties":[{"id":1,"name":"radiology"}],"id":7}` ferramenta: - ST103 Undocumented status code; Received: 201; Documented: 200, 304, 400, 404, 500 |
| `5143b272cea0` | POST /api/visits | schemathesis:ST103 | sc1, sc2, sc3 | não | `POST /petclinic/api/visits` → 404 `{"detail":"The requested resource could not be processed due to a data constraint violation","instance":"/petclinic/api/visits","status":404,"title":"DataIntegr` ferramenta: - ST103 Undocumented status code; Received: 201; Documented: 200, 304, 400, 404, 500 |
| `a269b87fbf37` | PUT / | schemathesis:ST103 | sc1, sc2, sc3 | sim | `PUT /petclinic/` → 302 ferramenta: - ST103 Undocumented status code; Received: 302; Documented: 200 |
| `4c751c84f28b` | PUT /api/owners/{ownerId} | schemathesis:ST103 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/owners/1` → 204 ferramenta: - ST103 Undocumented status code; Received: 204; Documented: 200, 400, 404, 500 |
| `63fdd6e688ba` | PUT /api/pets/{petId} | schemathesis:ST103 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/pets/1` → 204 ferramenta: - ST103 Undocumented status code; Received: 204; Documented: 200, 304, 400, 404, 500 |
| `09657fe5b1a9` | PUT /api/pettypes/{petTypeId} | schemathesis:ST103 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/pettypes/1` → 204 ferramenta: - ST103 Undocumented status code; Received: 204; Documented: 200, 304, 400, 404, 500 |
| `4163fa24a4c1` | PUT /api/specialties/{specialtyId} | schemathesis:ST103 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/specialties/1` → 204 ferramenta: - ST103 Undocumented status code; Received: 204; Documented: 200, 304, 400, 404, 500 |
| `ff83e7ef047a` | PUT /api/vets/{vetId} | schemathesis:ST103 | sc1, sc2, sc3 | não | `PUT /petclinic/api/vets/7` → 404 ferramenta: - ST103 Undocumented status code; Received: 204; Documented: 200, 304, 400, 404, 500 |
| `0a0461d967c9` | PUT /api/visits/{visitId} | schemathesis:ST103 | sc1, sc2, sc3 | não | `PUT /petclinic/api/visits/8` → 404 ferramenta: - ST103 Undocumented status code; Received: 204; Documented: 200, 304, 400, 404, 500 |
| `0d70b61abac7` | Stateful tests | schemathesis:ST103 | sc1, sc2, sc3 | não | `GET /petclinic/api/pets` → 200 `[{"name":"Leo","birthDate":"2010-09-07","type":{"name":"cat","id":1},"id":1,"visits":[],"ownerId":1},{"name":"Basil","birthDate":"2012-08-06","type":{"name":"ha` ferramenta: - ST103 Undocumented status code; Received: 404; Documented: 200, 304, 500 |

### FP sugerido (2 relatos)

Causa: método não declarado respondido com 400 em vez de 405; sem falha da API.

Ferramentas: schemathesis (2).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `84f648519a6d` | GET /api/pets | schemathesis:ST204 | sc1, sc2, sc3 | sim | `QUERY /petclinic/api/pets` → 400 `{"timestamp":"2026-11-24T22:13:31.972Z","status":400,"error":"Bad Request","path":"/petclinic/api/pets"}` ferramenta: - ST204 Wrong response to undeclared method |
| `0e005aa64409` | GET /api/visits | schemathesis:ST204 | sc1, sc2, sc3 | sim | `QUERY /petclinic/api/visits` → 400 `{"timestamp":"2026-11-24T22:15:47.541Z","status":400,"error":"Bad Request","path":"/petclinic/api/visits"}` ferramenta: - ST204 Wrong response to undeclared method |

### FP sugerido (1 relato)

Causa: resposta difere do schema documentado (erro da especificação, não da API).

Ferramentas: schemathesis (1).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `a0ad87219967` | Stateful tests | schemathesis:ST108 | sc2 | sim | `DELETE /petclinic/api/pets/_%C2%B1%C2%B4%7C%25%C3%93%F3%8D%96%8B%F0%9C%8A%8F%C3%83%F3%8B%8A%A4Ll%C3%94%F0%AF%91%B30%F2%AC%B9%98` → 400 `{"timestamp":"2026-11-24T22:49:40.551Z","status":400,"error":"Bad Request","path":"/petclinic/api/pets/_%C2%B1%C2%B4%7C%25%C3%93%F3%8D%96%8B%F0%9C%8A%8F%C3%83%F` ferramenta: - ST108 Response violates schema |

### FP sugerido (40 relatos)

Causa: resposta sem corpo/sem Content-Type onde a especificação declara um tipo; sem falha da API.

Ferramentas: schemathesis (40).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `c25f0d85b8e7` | DELETE /api/pets/{petId} | schemathesis:ST104 | sc2, sc3 | sim | `DELETE /petclinic/api/pets/10` → 204 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `4eca4984dfb2` | DELETE /api/pets/{petId} | schemathesis:ST109 | sc2, sc3 | sim | `DELETE /petclinic/api/pets/10` → 204 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `192f39908a25` | DELETE /api/pettypes/{petTypeId} | schemathesis:ST104 | sc2, sc3 | sim | `DELETE /petclinic/api/pettypes/2` → 204 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `c7bfac28967b` | DELETE /api/pettypes/{petTypeId} | schemathesis:ST109 | sc2, sc3 | sim | `DELETE /petclinic/api/pettypes/2` → 204 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `f724a2a5be3d` | DELETE /api/specialties/{specialtyId} | schemathesis:ST104 | sc1 | sim | `DELETE /petclinic/api/specialties/5` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `f624bd5464b3` | DELETE /api/specialties/{specialtyId} | schemathesis:ST109 | sc1 | sim | `DELETE /petclinic/api/specialties/5` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `cbeef7026575` | DELETE /api/vets/{vetId} | schemathesis:ST104 | sc1, sc3 | sim | `DELETE /petclinic/api/vets/21376` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `672ad6c7035a` | DELETE /api/vets/{vetId} | schemathesis:ST109 | sc1, sc3 | sim | `DELETE /petclinic/api/vets/21376` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `29e13ad8000e` | DELETE /api/visits/{visitId} | schemathesis:ST104 | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/visits/6` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `10aa7ea1ddcb` | DELETE /api/visits/{visitId} | schemathesis:ST109 | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/visits/6` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `2c2be65ca7b7` | GET /api/owners/{ownerId} | schemathesis:ST104 | sc1, sc2, sc3 | sim | `GET /petclinic/api/owners/13` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `1ad0a6894998` | GET /api/owners/{ownerId} | schemathesis:ST109 | sc1, sc2, sc3 | sim | `GET /petclinic/api/owners/13` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `5d14377d66dd` | GET /api/owners/{ownerId}/pets/{petId} | schemathesis:ST104 | sc1, sc2, sc3 | não | `GET /petclinic/api/owners/1/pets/1` → 200 `{"name":"Leo","birthDate":"2010-09-07","type":{"name":"cat","id":1},"id":1,"visits":[],"ownerId":1}` ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `89ce8e52d6fb` | GET /api/owners/{ownerId}/pets/{petId} | schemathesis:ST109 | sc1, sc2, sc3 | não | `GET /petclinic/api/owners/1/pets/1` → 200 `{"name":"Leo","birthDate":"2010-09-07","type":{"name":"cat","id":1},"id":1,"visits":[],"ownerId":1}` ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `e9d41ffc6068` | GET /api/pets/{petId} | schemathesis:ST104 | sc1, sc2, sc3 | não | `GET /petclinic/api/pets/1` → 200 `{"name":"Leo","birthDate":"2010-09-07","type":{"name":"cat","id":1},"id":1,"visits":[],"ownerId":1}` ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `756bdfbf15be` | GET /api/pets/{petId} | schemathesis:ST109 | sc1, sc2, sc3 | não | `GET /petclinic/api/pets/1` → 200 `{"name":"Leo","birthDate":"2010-09-07","type":{"name":"cat","id":1},"id":1,"visits":[],"ownerId":1}` ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `d2f189ca88c4` | GET /api/pettypes/{petTypeId} | schemathesis:ST104 | sc1, sc2, sc3 | não | `GET /petclinic/api/pettypes/1` → 200 `{"name":"cat","id":1}` ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `1ac74e51d8eb` | GET /api/pettypes/{petTypeId} | schemathesis:ST109 | sc1, sc2, sc3 | não | `GET /petclinic/api/pettypes/1` → 200 `{"name":"cat","id":1}` ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `6c296c693e1a` | GET /api/specialties/{specialtyId} | schemathesis:ST104 | sc1, sc2, sc3 | sim | `GET /petclinic/api/specialties/23` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `e4080483f2ce` | GET /api/specialties/{specialtyId} | schemathesis:ST109 | sc1, sc2, sc3 | sim | `GET /petclinic/api/specialties/23` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `a76ecb843610` | GET /api/vets/{vetId} | schemathesis:ST104 | sc1, sc2, sc3 | não | `GET /petclinic/api/vets/1` → 200 `{"firstName":"James","lastName":"Carter","specialties":[],"id":1}` ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `5722a6d98b2d` | GET /api/vets/{vetId} | schemathesis:ST109 | sc1, sc2, sc3 | não | `GET /petclinic/api/vets/1` → 200 `{"firstName":"James","lastName":"Carter","specialties":[],"id":1}` ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `e758e2471b0b` | GET /api/visits/{visitId} | schemathesis:ST104 | sc1, sc2, sc3 | sim | `GET /petclinic/api/visits/5` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `3b32862919d8` | GET /api/visits/{visitId} | schemathesis:ST109 | sc1, sc2, sc3 | sim | `GET /petclinic/api/visits/5` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `7dac5e48dec0` | PUT /api/owners/{ownerId} | schemathesis:ST104 | sc3 | sim | `PUT /petclinic/api/owners/13` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `2656c0cebc4f` | PUT /api/owners/{ownerId} | schemathesis:ST109 | sc3 | sim | `PUT /petclinic/api/owners/13` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `90cd38f5db7b` | PUT /api/owners/{ownerId}/pets/{petId} | schemathesis:ST104 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/owners/1/pets/15` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `b5d2e754e6a2` | PUT /api/owners/{ownerId}/pets/{petId} | schemathesis:ST109 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/owners/1/pets/15` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `97eeefeec198` | PUT /api/pets/{petId} | schemathesis:ST104 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/pets/14` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `cce0634a795c` | PUT /api/pets/{petId} | schemathesis:ST109 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/pets/14` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `2db6f0824d56` | PUT /api/pettypes/{petTypeId} | schemathesis:ST104 | sc1, sc2, sc3 | não | `PUT /petclinic/api/pettypes/1` → 204 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `c1bb42b11e03` | PUT /api/pettypes/{petTypeId} | schemathesis:ST109 | sc1, sc2, sc3 | não | `PUT /petclinic/api/pettypes/1` → 204 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `4f48fcaf7832` | PUT /api/specialties/{specialtyId} | schemathesis:ST104 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/specialties/23` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `a7b9833d3ad9` | PUT /api/specialties/{specialtyId} | schemathesis:ST109 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/specialties/23` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `6e669d3eb376` | PUT /api/vets/{vetId} | schemathesis:ST104 | sc1, sc2, sc3 | não | `PUT /petclinic/api/vets/1` → 204 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `5ffe7c1ee4b2` | PUT /api/vets/{vetId} | schemathesis:ST109 | sc1, sc2, sc3 | não | `PUT /petclinic/api/vets/1` → 204 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `1077009dc35e` | PUT /api/visits/{visitId} | schemathesis:ST104 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/visits/5` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `56c05e0b43ab` | PUT /api/visits/{visitId} | schemathesis:ST109 | sc1, sc2, sc3 | sim | `PUT /petclinic/api/visits/5` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `e2452b86fc41` | Stateful tests | schemathesis:ST104 | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/owners/10` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |
| `11ab21abfefc` | Stateful tests | schemathesis:ST109 | sc1, sc2, sc3 | sim | `DELETE /petclinic/api/owners/10` → 404 ferramenta: - ST109 JSON deserialization error; - ST104 Missing Content-Type header |

## vampi

### NOVO-vampi-1 — VP sugerido (2 relatos)

POST /books/v1 com título que já pertence a outro usuário devolve 500 (IntegrityError, restrição UNIQUE de books.book_title) em vez de 400; no piloto foi registrado como VAMPI-10.

Ferramentas: evomaster (1), schemathesis (2).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `3bb5b01b73e9` | POST /books/v1 | http_5xx | ev1, ev2, ev3, sc1, sc2, sc3 | sim | `POST /books/v1` → 200 `{"message": "Book has been added.", "status": "success"}` |
| `5180ebae611a` | Stateful tests | schemathesis:ST103 | sc1, sc2, sc3 | sim | `POST /books/v1` → 200 `{"message": "Book has been added.", "status": "success"}` ferramenta: - ST101 Server error; - ST103 Undocumented status code; Received: 500; Documented: 200, 400, 401 |

Justificativa: 500: POST /books/v1 com título que já pertence a outro usuário devolve 500 (IntegrityError, restrição UNIQUE de books.book_title) em vez de 400; no piloto foi registrado como VAMPI-10. Reproduzido à mão (data/processed/reproducao/manual_*.txt)


### NOVO-vampi-2 — VP sugerido (3 relatos)

GET /createdb devolve 500 (IntegrityError) quando o sorteio dos títulos dos livros iniciais repete um título; intermitente (8 em 300 chamadas numa API limpa).

Ferramentas: evomaster (2), schemathesis (2).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `80c49ed6967f` | GET /createdb | evomaster:101 | ev1 | sim | `GET /createdb` → 200 `{ "message": "Database populated." }` ferramenta: // Fault100. HTTP Status 500.; // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `c4ff37a6cddc` | GET /createdb | http_5xx | ev1, ev2, ev3, sc1, sc2, sc3 | sim | `GET /createdb` → 200 `{ "message": "Database populated." }` |
| `eb2b0e1c4ce2` | GET /createdb | schemathesis:ST103 | sc1, sc2, sc3 | sim | `GET /createdb` → 200 `{ "message": "Database populated." }` ferramenta: - ST101 Server error; - ST103 Undocumented status code; Received: 500; Documented: 200 |

Justificativa: 500: GET /createdb devolve 500 (IntegrityError) quando o sorteio dos títulos dos livros iniciais repete um título; intermitente (8 em 300 chamadas numa API limpa). Reproduzido à mão (data/processed/reproducao/manual_*.txt)


### NOVO-vampi-3 — VP sugerido (1 relato)

Ferramentas: schemathesis (1).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `cd3f9722b4a9` | Stateful tests | schemathesis:ST302 | sc1, sc2, sc3 | sim | `GET /books/v1/` → 404 `{ "detail": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.", "status": 404, "title": ` ferramenta: - ST302 Created resource not found |

Justificativa: POST /books/v1 aceita book_title vazio (200 "Book has been added") e o livro criado não pode ser lido por GET /books/v1/{book_title} (404); reproduzido em API limpa


### VAMPI-01 — VP sugerido (22 relatos)

SQL injection no parâmetro username.

Ferramentas: restler (8), schemathesis (14).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `3fdc99bcfb2f` | GET /users/v1/{username} | http_5xx | re1 | sim | `GET /users/v1/]:X2BCb` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.StatementError: (sqlalchemy.exc.InvalidRequestError) A value is required for bind parameter 'X2BCb' ` |
| `eb50f42a0469` | GET /users/v1/{username} | http_5xx | re1 | sim | `GET /users/v1/^y'L$M['n%]JXSDEh*` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) near "L$M": syntax error [SQL: SELECT * FROM users WHER` |
| `351cbd4282e2` | GET /users/v1/{username} | http_5xx | re2 | sim | `GET /users/v1/Su'SPdJNGZ+5FSs7kGq$` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) near "SPdJNGZ": syntax error [SQL: SELECT * FROM users ` |
| `d0023365df5c` | GET /users/v1/{username} | http_5xx | re2 | sim | `GET /users/v1/5nxj2k[VXl\|vGS0aPp(tI'26d,Z\|P(<GG0` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "26d" [SQL: SELECT * FROM users WHE` |
| `5320e8011ccf` | GET /users/v1/{username} | http_5xx | re3 | sim | `GET /users/v1/E'\*^3J+$SQ2V#s((8rw7,g` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "\" [SQL: SELECT * FROM users WHERE` |
| `c3c4724be66a` | GET /users/v1/{username} | http_5xx | re3 | sim | `GET /users/v1/hHsS^${PR'YGHA%M3B<u4S:%GJ#W=&hO[J($YHS9^*J=Snk8` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) near "YGHA": syntax error [SQL: SELECT * FROM users WHE` |
| `adefc91931d0` | GET /users/v1/{username} | http_5xx | sc1, sc2 | sim | `GET /users/v1/%F1%9F%B9%A1%F2%8C%A4%A7%0A%27%F1%AA%AA%91%1A` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) near "񪪑": syntax error [SQL: SELECT * FROM users WHERE ` |
| `c51f9d1f6889` | GET /users/v1/{username} | http_5xx | sc1, sc2 | sim | `GET /users/v1/%F1%9F%B9%A1%F2%8C%A4%A7%0A%27` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'񟹡򌤧 ''" [SQL: SELECT * FROM users ` |
| `2089893ccaa5` | GET /users/v1/{username} | http_5xx | sc1, sc2 | sim | `GET /users/v1/%F1%9F%B9%A1%F2%8C%A4%A7%27` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'񟹡򌤧''" [SQL: SELECT * FROM users W` |
| `43434c45ca1a` | GET /users/v1/{username} | http_5xx | sc1, sc2 | sim | `GET /users/v1/%F1%9F%B9%A1%27` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'񟹡''" [SQL: SELECT * FROM users WH` |
| `54d6b5d97be4` | GET /users/v1/{username} | http_5xx | sc1, sc2, sc3 | sim | `GET /users/v1/%27` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'''" [SQL: SELECT * FROM users WHE` |
| `4854f4b2876c` | GET /users/v1/{username} | http_5xx | sc3 | sim | `GET /users/v1/%F0%B2%BA%B7%2A%F3%BA%BC%9A%C2%BBR%F1%B1%A1%A3%27%C3%AF%C2%90%5B%F2%A6%BA%9F` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) near "ï": syntax error [SQL: SELECT * FROM users WHERE` |
| `c0e4f8faa338` | GET /users/v1/{username} | http_5xx | sc3 | sim | `GET /users/v1/%F0%B2%BA%B7%2A%F3%BA%BC%9A%C2%BBR%F1%B1%A1%A3%27%C3%AF` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) near "ï": syntax error [SQL: SELECT * FROM users WHERE ` |
| `0a28b13bb831` | GET /users/v1/{username} | http_5xx | sc3 | sim | `GET /users/v1/%F0%B2%BA%B7%2A%F3%BA%BC%9A%C2%BBR%F1%B1%A1%A3%27` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'𲺷*󺼚»R񱡣''" [SQL: SELECT * FROM use` |
| `2e10e7b3308d` | GET /users/v1/{username} | http_5xx | sc3 | sim | `GET /users/v1/%F0%B2%BA%B7%2A%F3%BA%BC%9A%C2%BBR%27` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'𲺷*󺼚»R''" [SQL: SELECT * FROM user` |
| `736d2f9b6f06` | GET /users/v1/{username} | http_5xx | sc3 | sim | `GET /users/v1/%F0%B2%BA%B7%2A%F3%BA%BC%9A%C2%BB%27` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'𲺷*󺼚»''" [SQL: SELECT * FROM users` |
| `b64c9d5ac25a` | GET /users/v1/{username} | http_5xx | sc3 | sim | `GET /users/v1/%F0%B2%BA%B7%2A%F3%BA%BC%9A%27` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'𲺷*󺼚''" [SQL: SELECT * FROM users ` |
| `cd596f510a75` | GET /users/v1/{username} | http_5xx | sc3 | sim | `GET /users/v1/%F0%B2%BA%B7%2A%27` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'𲺷*''" [SQL: SELECT * FROM users W` |
| `63f71b3c4f9a` | GET /users/v1/{username} | http_5xx | sc3 | sim | `GET /users/v1/%F0%B2%BA%B7%27` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'𲺷''" [SQL: SELECT * FROM users WH` |
| `7202155be343` | GET /users/v1/{username} | restler:InvalidValueChecker | re1 | sim | `GET /users/v1/]:X2BCb` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.StatementError: (sqlalchemy.exc.InvalidRequestError) A value is required for bind parameter 'X2BCb' ` |
| `c78369941b69` | GET /users/v1/{username} | schemathesis:ST103 | sc1, sc2, sc3 | sim | `GET /users/v1/%27` → 500 `<!doctype html> <html lang=en> <head> <title>sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unrecognized token: "'''" [SQL: SELECT * FROM users WHE` ferramenta: - ST101 Server error; - ST103 Undocumented status code; Received: 500; Documented: 200, 404 |
| `d270be035ef1` | desconhecida | restler:InvalidValueChecker | re2, re3 | sim | `GET /users/v1/Su'SPdJNGZ+5FSs7kGq$` → None `TIMEOUT (30 s)` |

Justificativa: 500 com erro de sintaxe SQL do SQLite ao usar o username na consulta: o valor é concatenado no SQL (injeção de SQL, VAMPI-01); reprodução manual com UNION extrai a senha


### VAMPI-07 — VP sugerido (1 relato)

ReDoS: expressão regular de validação de e-mail vulnerável.

Ferramentas: restler (1).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `e7f456148913` | PUT /users/v1/{username}/email | restler:InvalidValueChecker | re1, re2, re3 | sim | `PUT /users/v1/name1/email` → None `TIMEOUT (30 s)` |

Justificativa: RESTler registrou timeout no PUT /users/v1/{username}/email com e-mail longo; reprodução manual: e-mail com 81 caracteres terminando em '!' leva a API a não responder em 30 s (ReDoS na validação, VAMPI-07)


### FP sugerido (5 relatos)

Causa: API rejeita com 400 uma entrada que a especificação não restringe (especificação incompleta); 400 é a resposta correta.

Ferramentas: schemathesis (5).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `2ae9805c77ca` | POST /books/v1 | schemathesis:ST202 | sc1, sc2, sc3 | sim | `POST /books/v1` → 200 `{"message": "Book has been added.", "status": "success"}` ferramenta: - ST202 Schema-valid request rejected |
| `cfb9ad4f6da3` | POST /users/v1/login | schemathesis:ST202 | sc1, sc2, sc3 | sim | `POST /users/v1/login` → 400 `{ "status": "fail", "message": "'username' is a required property"}` ferramenta: - ST202 Schema-valid request rejected |
| `4267255482ca` | POST /users/v1/register | schemathesis:ST202 | sc1, sc2, sc3 | sim | `POST /users/v1/register` → 400 `{ "status": "fail", "message": "'username' is a required property"}` ferramenta: - ST202 Schema-valid request rejected |
| `45bf0905db24` | PUT /users/v1/{username}/email | schemathesis:ST202 | sc1, sc2, sc3 | sim | `PUT /users/v1/name1/email` → 400 `{ "status": "fail", "message": "Please provide a proper JSON body."}` ferramenta: - ST202 Schema-valid request rejected |
| `d1a7fc15e629` | PUT /users/v1/{username}/password | schemathesis:ST202 | sc1, sc2, sc3 | sim | `PUT /users/v1/name1/password` → 400 `{ "status": "fail", "message": "Malformed Data"}` ferramenta: - ST202 Schema-valid request rejected |

### FP sugerido (11 relatos)

Causa: Content-Type da resposta diferente do documentado (padrão do framework); sem falha da API.

Ferramentas: evomaster (6), schemathesis (5).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `748c1261bd53` | DELETE /users/v1/{username} | evomaster:101 | ev1, ev2, ev3 | sim | `DELETE /users/v1/oVGlNu` → 401 `{ "detail": "No authorization token provided", "status": 401, "title": "Unauthorized", "type": "about:blank" }` ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `32650435bf7d` | DELETE /users/v1/{username} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `DELETE /users/v1/admin` → 401 `{ "detail": "No authorization token provided", "status": 401, "title": "Unauthorized", "type": "about:blank" }` ferramenta: - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `8806276ccfa5` | GET /books/v1/{book_title} | evomaster:101 | ev1, ev2, ev3 | sim | `GET /books/v1/bSbQl2` → 401 `{ "detail": "No authorization token provided", "status": 401, "title": "Unauthorized", "type": "about:blank" }` ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `fd6017d0fef3` | GET /books/v1/{book_title} | schemathesis:ST105 | sc1, sc2, sc3 | sim | `GET /books/v1/book99` → 401 `{ "detail": "No authorization token provided", "status": 401, "title": "Unauthorized", "type": "about:blank" }` ferramenta: - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `ecff568650e1` | GET /me | evomaster:101 | ev1, ev2, ev3 | sim | `GET /me` → 401 `{ "detail": "No authorization token provided", "status": 401, "title": "Unauthorized", "type": "about:blank" }` ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `ab80c5353f05` | GET /me | schemathesis:ST105 | sc1, sc2, sc3 | sim | `GET /me` → 401 `{ "detail": "No authorization token provided", "status": 401, "title": "Unauthorized", "type": "about:blank" }` ferramenta: - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `766bb9b8d25b` | POST /books/v1 | evomaster:101 | ev1, ev2, ev3 | sim | `POST /books/v1` → 401 `{ "detail": "No authorization token provided", "status": 401, "title": "Unauthorized", "type": "about:blank" }` ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `6060e0c71cbd` | PUT /users/v1/{username}/email | evomaster:101 | ev1, ev2, ev3 | sim | `PUT /users/v1/_VzuiA08/email` → 401 `{ "detail": "No authorization token provided", "status": 401, "title": "Unauthorized", "type": "about:blank" }` ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `df7e62f18aab` | PUT /users/v1/{username}/email | schemathesis:ST105 | sc1, sc2, sc3 | sim | `PUT /users/v1/name1/email` → 401 `{ "detail": "No authorization token provided", "status": 401, "title": "Unauthorized", "type": "about:blank" }` ferramenta: - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |
| `862b84be1601` | PUT /users/v1/{username}/password | evomaster:101 | ev1, ev2, ev3 | sim | `PUT /users/v1/Cw196Twq/password` → 401 `{ "detail": "No authorization token provided", "status": 401, "title": "Unauthorized", "type": "about:blank" }` ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |
| `9a9f8f8fef96` | PUT /users/v1/{username}/password | schemathesis:ST105 | sc1, sc2, sc3 | sim | `PUT /users/v1/name1/password` → 401 `{ "detail": "No authorization token provided", "status": 401, "title": "Unauthorized", "type": "about:blank" }` ferramenta: - ST105 Undocumented Content-Type; Received: application/problem+json; Documented: application/json |

### FP sugerido (1 relato)

Causa: corpo de resposta não documentado na especificação.

Ferramentas: evomaster (1).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `b565d906d1d4` | POST /users/v1/register | evomaster:101 | ev1, ev2, ev3 | sim | `POST /users/v1/register` → 400 `{ "status": "fail", "message": "'username' is a required property"}` ferramenta: // Fault101. Received A Response From API With A Structure/Data That Is Not Matching Its Schema. Type: validat |

### FP sugerido (1 relato)

Causa: resposta difere do schema documentado (erro da especificação, não da API).

Ferramentas: schemathesis (1).

| chave | operação | tipo | ferramentas (repetições) | reproduzido | evidência resumida |
|---|---|---|---|---|---|
| `e2ef582a61ec` | GET /books/v1/{book_title} | schemathesis:ST108 | sc1, sc2, sc3 | não | `GET /books/v1/book99` → 404 `{ "status": "fail", "message": "Book not found!"}` ferramenta: - ST108 Response violates schema |

Legenda das repetições: `sc` Schemathesis, `re` RESTler, `ev` EvoMaster, seguido do número da repetição (ex.: `sc2` = Schemathesis, repetição 2).
