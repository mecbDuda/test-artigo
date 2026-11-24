# Resultados para o artigo: comparação de Schemathesis, RESTler e EvoMaster em APIs REST

Documento autocontido com todos os resultados da campanha completa, para quem vai escrever o
artigo. Os números foram copiados dos arquivos gerados pelos scripts de análise, sem nenhum
ajuste. O arquivo de origem de cada número vem indicado entre parênteses. As observações
que são interpretação, e não fato medido, estão marcadas como **[interpretação]**.

**Arquivos de origem** (caminhos no repositório https://github.com/mecbDuda/test-artigo):

| Nome curto | Caminho |
|---|---|
| `tabelas.md` | `data/results/tabelas.md` (todas as tabelas de métricas) |
| `metricas_por_execucao.csv` | `data/results/metricas_por_execucao.csv` (uma linha por execução) |
| `oraculo.csv` | `data/ground_truth/oraculo.csv` |
| `relatos.csv` | `data/validated/relatos.csv` (relatos únicos com sugestão, avaliações e classificação final) |
| `reproducao/` | `data/processed/reproducao/` (evidência da reprodução de cada relato em API limpa) |
| `resumo_execucao.csv` | `data/processed/resumo_execucao.csv` (datas, duração, limites; gerado de `data/raw/*/meta.json`) |
| `resumo_recursos.csv` | `data/processed/resumo_recursos.csv` (CPU/memória; gerado de `data/raw/recursos.csv` e `data/raw/*/conteineres.tsv`) |
| `vampi_operacoes_exercitadas.csv` | `data/processed/vampi_operacoes_exercitadas.csv` (gerado de `data/raw/vampi__*/flows.jsonl`) |
| `divergencias.csv` | `data/processed/divergencias.csv` |
| `desvios.md` | `docs/desvios.md` (desvios D01–D31 e ameaças à validade A1–A6) |
| `versoes.md` | `docs/versoes.md` (versões e máquina) |
| `campaigns.log` | `campaigns.log` (log da campanha) |
| `piloto/…` | `piloto/data/results/tabelas.md`, `piloto/data/results/metricas_por_execucao.csv`, `piloto/data/ground_truth/oraculo.csv` |

---

## a) Configuração executada

| Item | Valor |
|---|---|
| Ferramentas | Schemathesis **4.34.0**; RESTler **v9.2.4**; EvoMaster **5.1.0**, modo caixa-preta. Imagens Docker fixadas por digest (`config/experiment.env`, `versoes.md`) |
| APIs | VAmPI, petclinic-rest e catwatch (detalhes na seção d) |
| Desenho | 3 ferramentas × 3 APIs × **3 repetições** = **27 execuções** (`resumo_execucao.csv`) |
| Orçamento | **30 min** (1.800 s) por execução (`resumo_execucao.csv`) |
| Sementes | rep1 = 1001, rep2 = 1002, rep3 = 1003 (`resumo_execucao.csv`) |
| Execução paralela | **2 slots** paralelos e isolados: portas, projeto Docker Compose e redes próprias (`resumo_execucao.csv`, `desvios.md` D22) |
| Limites por contêiner, iguais para todas as ferramentas | ferramenta: 4 CPUs e 3.038 MiB; API: 2 CPUs e 1.536 MiB (APIs Java com `-Xmx1152m`); proxy mitmproxy: 1 CPU e 384 MiB (`resumo_execucao.csv`) |
| Máquina | PC com Windows 11 Pro e WSL2 (Ubuntu 24.04.5 LTS); Intel Core i5-13400F, 10 núcleos (6P + 4E), 16 threads; 16 GB de RAM física, dos quais 12 GB alocados ao WSL (11.964 MiB visíveis); Docker Engine 29.1.3, Compose 2.40.3, Python 3.12.3 (`versoes.md`) |
| Rede | Cada API fica numa rede Docker interna, sem internet. Todo o tráfego passa por um proxy (mitmproxy) que registra cada requisição e resposta (`desvios.md` D08) |
| Início e fim | primeira execução iniciada em 2026-11-23 20:53:52; última terminada em 2026-11-24 18:50:02 (`resumo_execucao.csv`) |
| Duração total | 21,94 h de relógio, das quais **7,38 h** com execuções ativas; o resto foi a pausa (`resumo_execucao.csv`) |
| Pausas | 1 pausa segura, de 2026-11-24 00:05:19 a 14:37:31, com 12 de 27 execuções concluídas e nenhuma em andamento (`desvios.md`, Registro automático; `campaigns.log`) |
| Duração por execução | média de 1.880,1 s (mín. 1.805,7; máx. 2.004,1), incluindo preparação e a minimização do EvoMaster depois do orçamento de busca (`resumo_execucao.csv`) |
| Resultado | **27/27 execuções concluídas**, **0 refeitas**, **0 falhas** (`resumo_execucao.csv`, `desvios.md`) |

## b) Desvios em relação ao planejado

O registro completo, com motivo e impacto de cada desvio, está em `desvios.md`. Resumo:

**Ambiente e execução**

- **D20, D21.** A campanha começou num GitHub Codespace (2 vCPUs), de forma sequencial. Foi
  interrompida depois de 6 execuções e refeita inteira num PC (i5-13400F). As 6 execuções do
  Codespace foram arquivadas e **não entram na análise**.
- **D22, D25: paralelização.** As 27 execuções rodaram em **2 slots simultâneos e isolados**,
  porque em sequência levariam cerca de 15 h. A estimativa com 2 slots era de 7,6 h, e 3
  slots foram descartados: a ferramenta ficaria com só 1.385 MiB de memória. A fila intercala
  ferramentas e APIs, para que nenhuma ferramenta tenha sempre a mesma vizinha.
- **D23, D24.** Os limites de CPU e memória por contêiner são iguais para todas as
  ferramentas. Nas APIs Java, o heap foi fixado em `-Xmx1152m` (75% do limite), para a JVM
  não encolher o heap por causa do limite.
- **D26.** Pausa segura e retomada: foi usada uma vez (seção a). Nenhuma execução precisou
  ser refeita.
- **D27.** Teste rápido em paralelo antes da campanha. Confirmou que não há mistura de
  tráfego entre slots, que a memória ficou dentro do limite e que a pausa e a recuperação
  depois de um desligamento brusco funcionam.
- **D08.** As APIs ficam sem internet. Na catwatch, isso faz `GET /fetch` falhar, porque essa
  operação depende do GitHub e do mailtrap.io (ver os inconclusivos na seção j).

**Ferramentas**

- **D11.** RESTler v8.5.0 → **v9.2.4** em todas as APIs: a v8.5.0 abortava o modo fuzz.
- **D13, D14, D17.** Ajustes de URL base e de reconexão no RESTler e no EvoMaster, para que
  as três ferramentas chamem as mesmas URLs.
- **D05, D18.** Folgas no fim do orçamento para as ferramentas gravarem os relatórios: o
  Schemathesis recebe `--max-time`, e a minimização do EvoMaster ganhou até 600 s. O
  orçamento de busca continua em 30 min.

**APIs e oráculo**

- **D09.** As APIs adicionais (petclinic-rest e catwatch) vêm do benchmark WFD
  (Web Fuzzing Dataset).
- **D10.** O oráculo dessas duas APIs começa vazio e é formado só por *pooling*. Por isso,
  nelas o **recall é relativo** aos defeitos encontrados por pelo menos uma ferramenta.

**Análise**

- **D28.** No extrator, IDs numéricos e UUIDs em caminhos fora da especificação foram
  normalizados. Isso reduziu os relatos únicos de 735 para 390 (no petclinic-rest, de 613
  para 268). Os 358 relatos do RESTler eram o mesmo comportamento com IDs diferentes.
- **D29.** Os 47 arquivos brutos acima de 50 MB foram versionados comprimidos (`.gz`).
  Nenhum ficou fora do git.

**Classificação**

- **D30.** A classificação partiu de **sugestões com evidência reproduzida**, preparadas com
  apoio de assistente de IA e revisadas pela equipe.
- **D31.** A equipe declarou concordância total com as sugestões, e a revisão foi registrada
  em bloco (ver seção f).

**Ameaças à validade registradas** (`desvios.md`):

- **A1.** O estado inicial do VAmPI não é determinístico: os títulos dos livros são sorteados.
- **A2.** A especificação do VAmPI expõe `GET /createdb`, que recria o banco.
- **A3.** O EvoMaster não consegue validar o esquema das respostas do petclinic-rest
  (OpenAPI 3.1), então ali só relata HTTP 500.
- **A4.** Algumas operações da catwatch são lentas.
- **A5.** A execução paralela pode influir no número de requisições, porque as duas
  execuções dividem cache, disco e o daemon do Docker.
- **A6.** Os avaliadores podem ter se ancorado na sugestão automática.

**Problemas durante a campanha.** Nenhuma execução falhou e nenhum contêiner foi morto por
falta de memória (seção c). As únicas interrupções foram a pausa planejada (seção a) e as
correções de ferramentas feitas antes da campanha (D11–D18), já registradas.

## c) Uso de recursos

As amostras foram coletadas a cada minuto (`resumo_recursos.csv`, a partir de
`data/raw/recursos.csv`). Na tabela, CPU em % de um núcleo (100% = 1 núcleo inteiro) e memória
em MiB.

| Escopo | Amostras | CPU média | CPU pico | Memória média | Memória pico | Pico em % do limite | Limite |
|---|---|---|---|---|---|---|---|
| Máquina (WSL, as 2 execuções juntas) | 393 | 10,6% da máquina | 21,3% da máquina | 2.149,1 | 2.847,6 | 23,8% | 11.964,3 |
| API alvo | 759 | 25,3% | 199,8% | 275,2 | 509,4 | 33,2% | 1.536 |
| Proxy | 759 | 21,7% | 76,4% | 63,5 | 88,2 | 23,0% | 384 |
| Ferramenta: Schemathesis | 261 | 65,4% | 110,0% | 383,4 | 513,2 | 16,9% | 3.038 |
| Ferramenta: RESTler | 242 | 5,9% | 18,8% | 55,3 | 79,2 | 2,6% | 3.038 |
| Ferramenta: EvoMaster | 247 | 10,6% | 203,1% | 230,4 | 343,7 | 11,3% | 3.038 |

**Algum contêiner atingiu o limite?** **Não.** Nos 99 registros de contêiner das 27 execuções,
o contador de vezes em que o limite de memória foi atingido ficou em **0** e não houve nenhum
**OOM kill** (`resumo_recursos.csv`, a partir de `conteineres.tsv`).

Os picos de memória medidos pelo cgroup, que incluem o cache de páginas, foram:

- ferramentas: até 594,2 MiB (Schemathesis);
- API: até 582,0 MiB;
- proxy: até 357,9 MiB, de um limite de 384 MiB.

O proxy foi o que mais se aproximou do limite, mas sem atingi-lo (`resumo_recursos.csv`). A
máquina nunca passou de 21,3% de CPU nem de 2,8 GiB de memória, ou seja, os 2 slots não
saturaram o hardware.

## d) Caracterização das APIs

| API | Linguagem / framework | Operações na especificação | Autenticação | Oráculo final: documentados + pooling = total |
|---|---|---|---|---|
| VAmPI | Python / Flask (SQLite) | 14 | JWT (as ferramentas usam o token do usuário `name1`) | 9 + 3 = **12** |
| petclinic-rest (WFD) | Java 17 / Spring Boot (H2) | 43 | nenhuma | 0 + 13 = **13** |
| catwatch (WFD) | Java 8 / Spring Boot (H2) | 23 | nenhuma | 0 + 8 = **8** |
| **Total** | | 80 | | 9 + 24 = **33** |

Fontes: número de operações em `metricas_por_execucao.csv` (cobertura = operações cobertas ÷
total; total em `data/processed/run_stats.csv`); oráculo em `oraculo.csv`.

O VAmPI é uma API deliberadamente vulnerável, cujas vulnerabilidades documentadas formam o
oráculo inicial. Nas duas APIs do WFD não há lista pública de defeitos, então todo o oráculo
vem de *pooling* (D10).

## e) Oráculo final

Fonte: `oraculo.csv`. Há 33 defeitos: 9 documentados e 24 de *pooling*. Os defeitos de
*pooling* foram confirmados pela equipe a partir dos relatos VP. A coluna "Operação" lista
até 6 das operações em que o defeito apareceu.

| ID | API | Operação | Tipo | Origem | Descrição |
|---|---|---|---|---|---|
| VAMPI-01 | vampi | GET /users/v1/{username} | injecao_sql | documentado | SQL injection no parâmetro username |
| VAMPI-02 | vampi | PUT /users/v1/{username}/password | autorizacao | documentado | Troca de senha de outro usuário sem autorização |
| VAMPI-03 | vampi | GET /books/v1/{book_title} | autorizacao_bola | documentado | Broken object-level authorization: acesso ao segredo de livro de outro usuário |
| VAMPI-04 | vampi | POST /users/v1/register | mass_assignment | documentado | Mass assignment: registro aceita atributo de administrador |
| VAMPI-05 | vampi | GET /users/v1/_debug | exposicao_dados | documentado | Exposição excessiva de dados no endpoint de debug |
| VAMPI-06 | vampi | POST /users/v1/login | enumeracao | documentado | Enumeração de usuários e senhas pelas mensagens de erro do login |
| VAMPI-07 | vampi | PUT /users/v1/{username}/email | redos | documentado | ReDoS: expressão regular de validação de e-mail vulnerável |
| VAMPI-08 | vampi | (global) | limite_recursos | documentado | Ausência de limite de recursos e de rate limiting |
| VAMPI-09 | vampi | (autenticação JWT) | autenticacao | documentado | Bypass de autenticação JWT por chave de assinatura fraca |
| NOVO-vampi-1 | vampi | POST /books/v1 | erro_500_restricao_unica | pooling | POST /books/v1 com título que já pertence a outro usuário devolve 500 (IntegrityError, restrição UNIQUE de books.book_title) em vez de 400; no piloto foi registrado como VAMPI-10 |
| NOVO-vampi-2 | vampi | GET /createdb | erro_500_intermitente | pooling | GET /createdb devolve 500 (IntegrityError) quando o sorteio dos títulos dos livros iniciais repete um título; intermitente (8 em 300 chamadas numa API limpa) |
| NOVO-vampi-3 | vampi | POST /books/v1; GET /books/v1/{book_title} | validacao_entrada | pooling | POST /books/v1 aceita book_title vazio e cria um livro que GET /books/v1/{book_title} não consegue ler (404) |
| NOVO-catwatch-1 | catwatch | GET /contributors | erro_500_entrada_invalida | pooling | GET /contributors: ContributorsApi.validate rejeita limit, offset ou sortBy inválidos com IllegalArgumentException, que não é tratada e vira 500 em vez de 400 |
| NOVO-catwatch-2 | catwatch | GET /contributors | erro_500_entrada_invalida | pooling | GET /contributors com combinação de parâmetros não implementada (datas) lança UnsupportedOperationException e devolve 500 |
| NOVO-catwatch-3 | catwatch | GET /contributors | erro_500_entrada_invalida | pooling | GET /contributors com data em formato inválido: ParseException em DateUtil.iso8601, devolve 500 em vez de 400 |
| NOVO-catwatch-4 | catwatch | GET /languages | erro_500_entrada_invalida | pooling | GET /languages com limit/offset negativos: IllegalArgumentException em LanguageService.filterLanguages, devolve 500 |
| NOVO-catwatch-5 | catwatch | GET /projects | erro_500_entrada_invalida | pooling | GET /projects com limit/offset negativos: IllegalArgumentException em ProjectServiceImpl.findProjects, devolve 500 |
| NOVO-catwatch-6 | catwatch | GET /statistics/projects | erro_500_entrada_invalida | pooling | GET /statistics/projects: IndexOutOfBoundsException (subList) em StatisticsApi.statisticsProjectGet quando há menos dados que o esperado |
| NOVO-catwatch-7 | catwatch | GET /statistics/contributors | erro_500_entrada_invalida | pooling | GET /statistics/contributors: IndexOutOfBoundsException (subList) em StatisticsApi.statisticsContributorGet quando há menos dados que o esperado |
| NOVO-catwatch-8 | catwatch | POST /config/scoring.project | erro_500_content_type | pooling | POST /config/scoring.project com Content-Type multipart/form-data sem boundary devolve 500 (MultipartException) em vez de 400/415 |
| NOVO-petclinic-rest-1 | petclinic-rest | 13 operações (ex.: DELETE /api/owners/{ownerId}, DELETE /api/pettypes/{petTypeId}, GET /api/owners/{ownerId}) | erro_500_rota_inexistente | pooling | Caminho inexistente (ex.: /api/owners/320/?/ ou /api/owners/1/1) devolve 500 (NoResourceFoundException) em vez de 404: o tratador genérico de exceções transforma tudo em 500 |
| NOVO-petclinic-rest-2 | petclinic-rest | 24 operações (ex.: DELETE /api/owners/{ownerId}, DELETE /api/pets/{petId}) | erro_500_entrada_invalida | pooling | Parâmetro de caminho ou de consulta com tipo inválido (ex.: petId="abc", page="x") devolve 500 (MethodArgumentTypeMismatchException) em vez de 400 |
| NOVO-petclinic-rest-3 | petclinic-rest | 24 operações (ex.: DELETE /api/owners/{ownerId}, DELETE /api/visits/{visitId}) | erro_500_entrada_invalida | pooling | Parâmetro que viola restrição de validação (ex.: id negativo, page/size < mínimo) devolve 500 (ConstraintViolationException) em vez de 400 |
| NOVO-petclinic-rest-4 | petclinic-rest | 15 operações (ex.: POST /api/owners, POST /api/pettypes, POST /api/users) | erro_500_entrada_invalida | pooling | Corpo JSON malformado ou com tipo errado devolve 500 (HttpMessageNotReadableException) em vez de 400 |
| NOVO-petclinic-rest-5 | petclinic-rest | GET /api/owners; GET /api/pettypes; GET /api/specialties; GET /api/vets; OPTIONS / | erro_500_content_type | pooling | Requisição com Content-Type multipart/form-data sem boundary devolve 500 (MultipartException) em vez de 400/415 |
| NOVO-petclinic-rest-6 | petclinic-rest | POST /api/owners; POST /api/owners/{ownerId}/pets; POST /api/owners/{ownerId}/pets/{petId}/visits; PUT /api/owners/{ownerId}/pets/{petId} | erro_500_content_type | pooling | Content-Type não suportado no corpo devolve 500 (HttpMediaTypeNotSupportedException) em vez de 415 |
| NOVO-petclinic-rest-7 | petclinic-rest | GET /api/owners; GET /api/v2/owners; GET /api/v2/pets | erro_500_entrada_invalida | pooling | Parâmetro de consulta sem nome (ex.: ?=false) devolve 500 (InvalidParameterException) em vez de 400 |
| NOVO-petclinic-rest-8 | petclinic-rest | POST /api/specialties; POST /api/vets; POST /api/visits | erro_500_estado | pooling | POST de specialty/vet/visit com "id" de entidade inexistente no corpo devolve 500 (ObjectOptimisticLockingFailureException em ClinicServiceImpl.saveSpecialty/saveVet/saveVisit) |
| NOVO-petclinic-rest-9 | petclinic-rest | GET /api/v2/owners; GET /api/v2/pets | erro_500_entrada_invalida | pooling | GET /api/v2/owners e /api/v2/pets com page*size acima de Integer.MAX_VALUE devolvem 500 (InvalidDataAccessApiUsageException: page offset exceeds Integer.MAX_VALUE) |
| NOVO-petclinic-rest-10 | petclinic-rest | PUT /api/owners/{ownerId}; PUT /api/pets/{petId} | erro_500_entrada_invalida | pooling | PUT de owner/pet com campos que violam as validações da entidade só falha no commit: 500 (TransactionSystemException) em vez de 400 |
| NOVO-petclinic-rest-11 | petclinic-rest | POST /api/users | erro_500_entrada_invalida | pooling | POST /api/users sem papéis (roles) devolve 500 (IllegalArgumentException "User must have at least a role set!" em UserServiceImpl.saveUser) em vez de 400 |
| NOVO-petclinic-rest-12 | petclinic-rest | POST /api/users | erro_500_entrada_invalida | pooling | POST /api/users com papel sem nome: NullPointerException em UserServiceImpl.saveUser (Role.getName), 500 |
| NOVO-petclinic-rest-13 | petclinic-rest | POST /api/visits | erro_500_estado | pooling | POST /api/visits com petId inexistente devolve 500 (ObjectRetrievalFailureException) em vez de 404/400 |

**Critério de agrupamento em defeitos** (`analysis/sugerir.py`, `docs/guia_revisao.md`):

- Exceções do framework, como as do Spring na conversão ou validação de entrada, contam
  como **um defeito por tipo de exceção**, mesmo quando aparecem em muitas operações.
- Exceções da aplicação contam como **um defeito por ponto do código**: o primeiro quadro
  da aplicação na pilha de chamadas.
- Um relato de conformidade que só repete um 500 já agrupado herda o defeito desse 500.

## f) Como foi feita a classificação

1. **Extração.** `analysis/extract_findings.py` reuniu os achados das 27 execuções:
   - os HTTP 5xx registrados pelo proxy;
   - os relatórios JUnit do Schemathesis;
   - os *bug buckets* do RESTler;
   - os testes de falha do EvoMaster.

   Depois de deduplicados por operação, tipo e assinatura, restaram **390 relatos únicos**
   (`relatos.csv`): 47 do VAmPI, 75 da catwatch e 268 do petclinic-rest.
2. **Reprodução.** Cada relato foi reproduzido numa API recém-iniciada, com os mesmos limites
   de CPU e memória (`analysis/reproduzir.py`). Para cada um ficaram registrados a
   requisição, a resposta e o log da API (`reproducao/`). Os casos que dependem de estado
   foram reproduzidos à mão (`reproducao/manual_vampi.txt`, `reproducao/manual_petclinic.txt`).
   **359 dos 390 relatos reproduziram** e 31 não (`relatos.csv`, coluna `reproduzido`). Os não
   reproduzidos são, na maioria, relatos de conformidade que dependiam de IDs criados durante
   a execução original.
3. **Sugestão.** Cada relato recebeu uma sugestão VP, FP ou INC, com o defeito e uma
   justificativa. As sugestões seguem regras explícitas em `analysis/sugerir.py`, foram
   preparadas com apoio de um assistente de IA e estão agrupadas por API e defeito
   em `docs/guia_revisao.md`.
4. **Revisão por dois avaliadores.** Cada avaliador marca "ok" se concorda com a sugestão ou
   escreve a classificação correta. A equipe declarou que **os dois avaliadores concordaram
   com todas as 390 sugestões**, e isso foi registrado em bloco nas colunas `avaliador_1` e
   `avaliador_2` (`desvios.md` D31).
5. **Divergências: 0** (`divergencias.csv` está vazio; `analysis/consolidar_revisao.py`).
   Como não houve divergências, não foi preciso decidir nenhum caso.
6. **Classificação final:** **206 VP, 182 FP e 2 INC** (`relatos.csv`). Os 24 defeitos novos
   confirmados entraram no oráculo com `origem=pooling` (`oraculo.csv`).

Limitação a declarar no artigo: as marcações não foram feitas relato a relato. Por isso não
é possível medir a concordância entre avaliadores, como o κ de Cohen. Além disso, a revisão
partiu de uma sugestão pronta, com risco de ancoragem (`desvios.md`, D30, D31 e A6).

**Definições das métricas** (`analysis/compute_metrics.py`):

- **Recall** = defeitos do oráculo detectados ÷ defeitos do oráculo da API.
- **Precisão** = relatos VP ÷ (VP + FP), sobre os relatos únicos, sem contar os INC.
- **F1** = média harmônica de precisão e recall.
- **Cobertura de operações** = % das operações da especificação que receberam pelo menos uma
  resposta 2xx.
- **TTFF** = tempo até o primeiro relato classificado como VP.
- **DPH** = defeitos distintos detectados por hora de orçamento.
- **Â12** = medida de efeito de Vargha-Delaney.
- **p** = teste de Mann-Whitney bilateral.

"Relatos brutos" é o número de ocorrências antes da deduplicação.

## g) Tabelas de resultados

Todas as tabelas desta seção foram copiadas de `tabelas.md`, com valores por execução em
`metricas_por_execucao.csv`. Os decimais usam ponto, como nos arquivos de origem.

### Tabela 2: resumo dos relatos por ferramenta (união das 9 execuções de cada ferramenta)

| Ferramenta | Relatos brutos | Após deduplicação | VP | FP | Inconclusivos |
|---|---|---|---|---|---|
| Schemathesis | 83318 | 269 | 121 | 148 | 0 |
| RESTler | 122639 | 124 | 109 | 14 | 1 |
| EvoMaster (caixa-preta) | 310743 | 62 | 33 | 27 | 2 |

O mesmo relato único pode ter sido emitido por mais de uma ferramenta, por isso a soma por
ferramenta (455) passa dos 390 relatos únicos.

### Tabela 3: defeitos detectados e recall por ferramenta e API

| API | Defeitos no oráculo | Schemathesis VP (união) | Schemathesis Recall (união) | Schemathesis Recall (média) | RESTler VP (união) | RESTler Recall (união) | RESTler Recall (média) | EvoMaster VP (união) | EvoMaster Recall (união) | EvoMaster Recall (média) |
|---|---|---|---|---|---|---|---|---|---|---|
| catwatch | 8 | 8 | 100.0% | 95.8% | 7 | 87.5% | 87.5% | 7 | 87.5% | 87.5% |
| petclinic-rest | 13 | 11 | 84.6% | 76.9% | 7 | 53.8% | 53.8% | 7 | 53.8% | 53.8% |
| vampi | 12 | 4 | 33.3% | 33.3% | 2 | 16.7% | 16.7% | 2 | 16.7% | 16.7% |
| Total | 33 | 23 | 69.7% | 68.7% | 16 | 48.5% | 52.7% | 16 | 48.5% | 52.7% |

"VP (união)" é o número de defeitos distintos detectados em pelo menos uma das 3
repetições. "Recall (média)" é a média do recall por execução. Na linha Total, a média é
calculada sobre as 9 execuções de cada ferramenta.

### Sobreposição: defeitos por combinação de ferramentas

| API | Encontrado por | Defeitos |
|---|---|---|
| catwatch | Schemathesis | 1 |
| catwatch | Schemathesis + RESTler + EvoMaster | 7 |
| catwatch | Nenhuma ferramenta | 0 |
| petclinic-rest | EvoMaster | 1 |
| petclinic-rest | RESTler | 1 |
| petclinic-rest | Schemathesis | 4 |
| petclinic-rest | Schemathesis + EvoMaster | 1 |
| petclinic-rest | Schemathesis + RESTler | 1 |
| petclinic-rest | Schemathesis + RESTler + EvoMaster | 5 |
| petclinic-rest | Nenhuma ferramenta | 0 |
| vampi | RESTler | 1 |
| vampi | Schemathesis | 1 |
| vampi | Schemathesis + EvoMaster | 2 |
| vampi | Schemathesis + RESTler | 1 |
| vampi | Nenhuma ferramenta | 7 |

Somando as três APIs, 12 dos 33 defeitos foram achados pelas três ferramentas, 5 por exatamente
duas, 9 por uma só e 7 por nenhuma (`tabelas.md`). Nas APIs do WFD, "Nenhuma ferramenta" é sempre 0 por
construção, porque o oráculo dessas APIs vem só de *pooling*.

### Tabela 4: precisão e relatos inconclusivos por ferramenta (relatos únicos)

| Ferramenta | VP | FP | Precisão | Inconclusivos | Principal causa de FP |
|---|---|---|---|---|---|
| Schemathesis | 121 | 148 | 45.0% | 0 | resposta sem corpo/sem Content-Type onde a especificação declara um tipo; sem falha da API (40 de 148) |
| RESTler | 109 | 14 | 88.6% | 1 | o *checker* InvalidDynamicObjectChecker anexou `?injected_query_string=123` ao caminho de um objeto válido e esperava erro; a API ignora o parâmetro e devolve o objeto (8 de 14) |
| EvoMaster (caixa-preta) | 33 | 27 | 55.0% | 2 | endpoint interno `/error` do Spring Boot exposto pela especificação; chamado diretamente responde 500 por desenho do framework (13 de 27) |

### Tabela 5: precisão, recall e F1 (média das 9 execuções de cada ferramenta)

| Ferramenta | Precisão (média) | Recall (média) | F1 (média) | F1 (mín–máx) |
|---|---|---|---|---|
| Schemathesis | 42.5% | 68.7% | 0.47 | 0.40–0.60 |
| RESTler | 86.1% | 52.7% | 0.57 | 0.29–0.76 |
| EvoMaster (caixa-preta) | 54.7% | 52.7% | 0.48 | 0.19–0.70 |

### Tabela 6: exploração e custo (média das 9 execuções)

| Ferramenta | Cobertura de operações (%) | Nº de requisições | TTFF (min) | DPH |
|---|---|---|---|---|
| Schemathesis | 72.7 | 97160 | 0.1 | 14.44 |
| RESTler | 67.2 | 57891 | 0.1 | 10.67 |
| EvoMaster (caixa-preta) | 70.6 | 225371 | 0.1 | 10.67 |

### Tabela 7: métricas por ferramenta e API, como média (mínimo–máximo) entre as 3 repetições

| API | Ferramenta | Rep. | Relatos brutos | Relatos únicos | VP | FP | INC | Defeitos detectados | Recall | Precisão | F1 | Cobertura de operações (%) | Requisições | TTFF (min) | DPH |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| catwatch | Schemathesis | 3 | 10180.3 (9962.0–10540.0) | 43.0 (41.0–45.0) | 12.3 (11.0–14.0) | 30.7 (30.0–31.0) | 0.0 (0.0–0.0) | 7.7 (7.0–8.0) | 95.8% (87.5%–100.0%) | 28.6% (26.8%–31.1%) | 0.44 (0.41–0.47) | 39.1 (39.1–39.1) | 66424 (65885–66854) | 0.1 (0.1–0.1) | 15.33 (14.00–16.00) |
| catwatch | RESTler | 3 | 4565.3 (4130.0–4904.0) | 19.0 (19.0–19.0) | 12.0 (12.0–12.0) | 6.0 (6.0–6.0) | 1.0 (1.0–1.0) | 7.0 (7.0–7.0) | 87.5% (87.5%–87.5%) | 66.7% (66.7%–66.7%) | 0.76 (0.76–0.76) | 39.1 (39.1–39.1) | 86566 (81969–92758) | 0.2 (0.1–0.2) | 14.00 (14.00–14.00) |
| catwatch | EvoMaster | 3 | 772.7 (750.0–791.0) | 35.0 (34.0–36.0) | 13.0 (12.0–14.0) | 20.0 (20.0–20.0) | 2.0 (2.0–2.0) | 7.0 (7.0–7.0) | 87.5% (87.5%–87.5%) | 39.4% (37.5%–41.2%) | 0.54 (0.53–0.56) | 39.1 (39.1–39.1) | 1626 (1593–1687) | 0.1 (0.0–0.1) | 14.00 (14.00–14.00) |
| petclinic-rest | Schemathesis | 3 | 17047.0 (16286.0–17977.0) | 176.7 (172.0–184.0) | 81.7 (78.0–86.0) | 95.0 (93.0–98.0) | 0.0 (0.0–0.0) | 10.0 (9.0–11.0) | 76.9% (69.2%–84.6%) | 46.2% (45.3%–46.7%) | 0.58 (0.56–0.60) | 86.0 (86.0–86.0) | 73677 (69024–81833) | 0.1 (0.1–0.2) | 20.00 (18.00–22.00) |
| petclinic-rest | RESTler | 3 | 36309.3 (33260.0–38835.0) | 95.3 (95.0–96.0) | 87.3 (87.0–88.0) | 8.0 (8.0–8.0) | 0.0 (0.0–0.0) | 7.0 (7.0–7.0) | 53.8% (53.8%–53.8%) | 91.6% (91.6%–91.7%) | 0.68 (0.68–0.68) | 76.7 (76.7–76.7) | 86196 (83319–89648) | 0.1 (0.1–0.2) | 14.00 (14.00–14.00) |
| petclinic-rest | EvoMaster | 3 | 102370.7 (98772.0–105507.0) | 16.0 (16.0–16.0) | 16.0 (16.0–16.0) | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) | 7.0 (7.0–7.0) | 53.8% (53.8%–53.8%) | 100.0% (100.0%–100.0%) | 0.70 (0.70–0.70) | 79.8 (76.7–83.7) | 491784 (488797–493538) | 0.1 (0.1–0.1) | 14.00 (14.00–14.00) |
| vampi | Schemathesis | 3 | 545.3 (529.0–563.0) | 23.3 (22.0–26.0) | 12.3 (11.0–15.0) | 11.0 (11.0–11.0) | 0.0 (0.0–0.0) | 4.0 (4.0–4.0) | 33.3% (33.3%–33.3%) | 52.6% (50.0%–57.7%) | 0.41 (0.40–0.42) | 92.9 (92.9–92.9) | 151379 (144351–162333) | 0.1 (0.1–0.1) | 8.00 (8.00–8.00) |
| vampi | RESTler | 3 | 5.0 (5.0–5.0) | 4.0 (4.0–4.0) | 4.0 (4.0–4.0) | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) | 2.0 (2.0–2.0) | 16.7% (16.7%–16.7%) | 100.0% (100.0%–100.0%) | 0.29 (0.29–0.29) | 85.7 (85.7–85.7) | 910 (902–918) | 0.2 (0.1–0.2) | 4.00 (4.00–4.00) |
| vampi | EvoMaster | 3 | 437.7 (421.0–454.0) | 9.3 (9.0–10.0) | 2.3 (2.0–3.0) | 7.0 (7.0–7.0) | 0.0 (0.0–0.0) | 2.0 (2.0–2.0) | 16.7% (16.7%–16.7%) | 24.8% (22.2%–30.0%) | 0.20 (0.19–0.21) | 92.9 (92.9–92.9) | 182704 (178587–190026) | 0.1 (0.1–0.1) | 4.00 (4.00–4.00) |

### Comparação estatística geral, por par de ferramentas (n = 9 execuções por ferramenta)

Â12 > 0,5 favorece a primeira ferramenta do par. O valor "0.000" é p < 0,0005, arredondado
para 3 casas.

| Métrica | Comparação | n | Â12 | p (Mann-Whitney) |
|---|---|---|---|---|
| recall | Schemathesis vs RESTler | 9/9 | 0.65 | 0.304 |
| recall | Schemathesis vs EvoMaster | 9/9 | 0.65 | 0.304 |
| recall | RESTler vs EvoMaster | 9/9 | 0.50 | 1.000 |
| precisao | Schemathesis vs RESTler | 9/9 | 0.00 | 0.000 |
| precisao | Schemathesis vs EvoMaster | 9/9 | 0.53 | 0.859 |
| precisao | RESTler vs EvoMaster | 9/9 | 0.72 | 0.114 |
| f1 | Schemathesis vs RESTler | 9/9 | 0.33 | 0.249 |
| f1 | Schemathesis vs EvoMaster | 9/9 | 0.43 | 0.658 |
| f1 | RESTler vs EvoMaster | 9/9 | 0.67 | 0.248 |
| cobertura_operacoes_pct | Schemathesis vs RESTler | 9/9 | 0.72 | 0.112 |
| cobertura_operacoes_pct | Schemathesis vs EvoMaster | 9/9 | 0.56 | 0.713 |
| cobertura_operacoes_pct | RESTler vs EvoMaster | 9/9 | 0.41 | 0.525 |
| dph | Schemathesis vs RESTler | 9/9 | 0.74 | 0.082 |
| dph | Schemathesis vs EvoMaster | 9/9 | 0.74 | 0.082 |
| dph | RESTler vs EvoMaster | 9/9 | 0.50 | 1.000 |

### Comparação estatística por API (n = 3 execuções por grupo)

Com 3 execuções por grupo, o menor p bilateral possível do Mann-Whitney é cerca de 0,10, ou um
pouco menor quando há empates. "—" indica dados idênticos nos dois grupos, em que o teste não
se aplica.

| API | Métrica | Comparação | n | Â12 | p (Mann-Whitney) |
|---|---|---|---|---|---|
| catwatch | recall | Schemathesis vs RESTler | 3/3 | 0.83 | 0.188 |
| catwatch | recall | Schemathesis vs EvoMaster | 3/3 | 0.83 | 0.188 |
| catwatch | recall | RESTler vs EvoMaster | 3/3 | 0.50 | — |
| catwatch | precisao | Schemathesis vs RESTler | 3/3 | 0.00 | 0.064 |
| catwatch | precisao | Schemathesis vs EvoMaster | 3/3 | 0.00 | 0.100 |
| catwatch | precisao | RESTler vs EvoMaster | 3/3 | 1.00 | 0.064 |
| catwatch | f1 | Schemathesis vs RESTler | 3/3 | 0.00 | 0.064 |
| catwatch | f1 | Schemathesis vs EvoMaster | 3/3 | 0.00 | 0.100 |
| catwatch | f1 | RESTler vs EvoMaster | 3/3 | 1.00 | 0.064 |
| catwatch | cobertura_operacoes_pct | Schemathesis vs RESTler | 3/3 | 0.50 | — |
| catwatch | cobertura_operacoes_pct | Schemathesis vs EvoMaster | 3/3 | 0.50 | — |
| catwatch | cobertura_operacoes_pct | RESTler vs EvoMaster | 3/3 | 0.50 | — |
| catwatch | requisicoes | Schemathesis vs RESTler | 3/3 | 0.00 | 0.100 |
| catwatch | requisicoes | Schemathesis vs EvoMaster | 3/3 | 1.00 | 0.100 |
| catwatch | requisicoes | RESTler vs EvoMaster | 3/3 | 1.00 | 0.100 |
| catwatch | dph | Schemathesis vs RESTler | 3/3 | 0.83 | 0.188 |
| catwatch | dph | Schemathesis vs EvoMaster | 3/3 | 0.83 | 0.188 |
| catwatch | dph | RESTler vs EvoMaster | 3/3 | 0.50 | — |
| petclinic-rest | recall | Schemathesis vs RESTler | 3/3 | 1.00 | 0.064 |
| petclinic-rest | recall | Schemathesis vs EvoMaster | 3/3 | 1.00 | 0.064 |
| petclinic-rest | recall | RESTler vs EvoMaster | 3/3 | 0.50 | — |
| petclinic-rest | precisao | Schemathesis vs RESTler | 3/3 | 0.00 | 0.077 |
| petclinic-rest | precisao | Schemathesis vs EvoMaster | 3/3 | 0.00 | 0.064 |
| petclinic-rest | precisao | RESTler vs EvoMaster | 3/3 | 0.00 | 0.059 |
| petclinic-rest | f1 | Schemathesis vs RESTler | 3/3 | 0.00 | 0.077 |
| petclinic-rest | f1 | Schemathesis vs EvoMaster | 3/3 | 0.00 | 0.064 |
| petclinic-rest | f1 | RESTler vs EvoMaster | 3/3 | 0.00 | 0.059 |
| petclinic-rest | cobertura_operacoes_pct | Schemathesis vs RESTler | 3/3 | 1.00 | 0.047 |
| petclinic-rest | cobertura_operacoes_pct | Schemathesis vs EvoMaster | 3/3 | 1.00 | 0.064 |
| petclinic-rest | cobertura_operacoes_pct | RESTler vs EvoMaster | 3/3 | 0.17 | 0.197 |
| petclinic-rest | requisicoes | Schemathesis vs RESTler | 3/3 | 0.00 | 0.100 |
| petclinic-rest | requisicoes | Schemathesis vs EvoMaster | 3/3 | 0.00 | 0.100 |
| petclinic-rest | requisicoes | RESTler vs EvoMaster | 3/3 | 0.00 | 0.100 |
| petclinic-rest | dph | Schemathesis vs RESTler | 3/3 | 1.00 | 0.064 |
| petclinic-rest | dph | Schemathesis vs EvoMaster | 3/3 | 1.00 | 0.064 |
| petclinic-rest | dph | RESTler vs EvoMaster | 3/3 | 0.50 | — |
| vampi | recall | Schemathesis vs RESTler | 3/3 | 1.00 | 0.047 |
| vampi | recall | Schemathesis vs EvoMaster | 3/3 | 1.00 | 0.047 |
| vampi | recall | RESTler vs EvoMaster | 3/3 | 0.50 | — |
| vampi | precisao | Schemathesis vs RESTler | 3/3 | 0.00 | 0.059 |
| vampi | precisao | Schemathesis vs EvoMaster | 3/3 | 1.00 | 0.072 |
| vampi | precisao | RESTler vs EvoMaster | 3/3 | 1.00 | 0.059 |
| vampi | f1 | Schemathesis vs RESTler | 3/3 | 1.00 | 0.059 |
| vampi | f1 | Schemathesis vs EvoMaster | 3/3 | 1.00 | 0.072 |
| vampi | f1 | RESTler vs EvoMaster | 3/3 | 1.00 | 0.059 |
| vampi | cobertura_operacoes_pct | Schemathesis vs RESTler | 3/3 | 1.00 | 0.047 |
| vampi | cobertura_operacoes_pct | Schemathesis vs EvoMaster | 3/3 | 0.50 | — |
| vampi | cobertura_operacoes_pct | RESTler vs EvoMaster | 3/3 | 0.00 | 0.047 |
| vampi | requisicoes | Schemathesis vs RESTler | 3/3 | 1.00 | 0.100 |
| vampi | requisicoes | Schemathesis vs EvoMaster | 3/3 | 0.00 | 0.100 |
| vampi | requisicoes | RESTler vs EvoMaster | 3/3 | 0.00 | 0.100 |
| vampi | dph | Schemathesis vs RESTler | 3/3 | 1.00 | 0.047 |
| vampi | dph | Schemathesis vs EvoMaster | 3/3 | 1.00 | 0.047 |
| vampi | dph | RESTler vs EvoMaster | 3/3 | 0.50 | — |

## h) Defeitos detectados

A tabela mostra, para cada defeito detectado, quantos relatos únicos foram classificados como
VP para ele (`relatos.csv`) e em quantas das 3 repetições cada ferramenta o detectou
(`metricas_por_execucao.csv`, coluna `defeitos_ids`). As descrições completas estão na seção e.
Foram detectados 26 dos 33 defeitos.

| ID | API | Resumo | Relatos VP | Schemathesis | RESTler | EvoMaster |
|---|---|---|---|---|---|---|
| VAMPI-01 | vampi | injeção de SQL em GET /users/v1/{username} | 22 | 3/3 | 3/3 | — |
| VAMPI-07 | vampi | ReDoS na validação de e-mail (timeout) | 1 | — | 3/3 | — |
| NOVO-vampi-1 | vampi | 500 ao criar livro com título de outro usuário | 2 | 3/3 | — | 3/3 |
| NOVO-vampi-2 | vampi | 500 intermitente em /createdb | 3 | 3/3 | — | 3/3 |
| NOVO-vampi-3 | vampi | livro com título vazio criado e ilegível | 1 | 3/3 | — | — |
| NOVO-catwatch-1 | catwatch | limit/offset/sortBy inválidos → 500 em /contributors | 5 | 3/3 | 3/3 | 3/3 |
| NOVO-catwatch-2 | catwatch | combinação não implementada → 500 em /contributors | 2 | 3/3 | 3/3 | 3/3 |
| NOVO-catwatch-3 | catwatch | data inválida → 500 em /contributors | 1 | 2/3 | 3/3 | 3/3 |
| NOVO-catwatch-4 | catwatch | limit/offset negativos → 500 em /languages | 4 | 3/3 | 3/3 | 3/3 |
| NOVO-catwatch-5 | catwatch | limit/offset negativos → 500 em /projects | 4 | 3/3 | 3/3 | 3/3 |
| NOVO-catwatch-6 | catwatch | IndexOutOfBounds em /statistics/projects | 2 | 3/3 | 3/3 | 3/3 |
| NOVO-catwatch-7 | catwatch | IndexOutOfBounds em /statistics/contributors | 2 | 3/3 | 3/3 | 3/3 |
| NOVO-catwatch-8 | catwatch | multipart sem boundary → 500 | 2 | 3/3 | — | — |
| NOVO-petclinic-rest-1 | petclinic-rest | rota inexistente → 500 (NoResourceFound) | 39 | — | 3/3 | — |
| NOVO-petclinic-rest-2 | petclinic-rest | parâmetro de tipo errado → 500 | 26 | 3/3 | 3/3 | — |
| NOVO-petclinic-rest-3 | petclinic-rest | violação de restrição → 500 | 27 | 3/3 | 3/3 | 3/3 |
| NOVO-petclinic-rest-4 | petclinic-rest | JSON malformado → 500 | 35 | 3/3 | 3/3 | 3/3 |
| NOVO-petclinic-rest-5 | petclinic-rest | multipart sem boundary → 500 | 10 | 3/3 | — | — |
| NOVO-petclinic-rest-6 | petclinic-rest | Content-Type não suportado → 500 | 4 | 3/3 | — | — |
| NOVO-petclinic-rest-7 | petclinic-rest | parâmetro de consulta sem nome → 500 | 3 | 3/3 | — | — |
| NOVO-petclinic-rest-8 | petclinic-rest | POST com id inexistente → 500 (optimistic locking) | 4 | 2/3 | 3/3 | 3/3 |
| NOVO-petclinic-rest-9 | petclinic-rest | page×size acima de Integer.MAX_VALUE → 500 | 2 | 3/3 | — | 3/3 |
| NOVO-petclinic-rest-10 | petclinic-rest | PUT inválido falha só no commit → 500 | 2 | 3/3 | 3/3 | 3/3 |
| NOVO-petclinic-rest-11 | petclinic-rest | usuário sem papéis → 500 | 1 | 3/3 | 3/3 | 3/3 |
| NOVO-petclinic-rest-12 | petclinic-rest | papel sem nome → NullPointerException | 1 | 1/3 | — | — |
| NOVO-petclinic-rest-13 | petclinic-rest | visita com petId inexistente → 500 | 1 | — | — | 3/3 |

Em 52 dos 55 pares defeito × ferramenta com detecção (23 do Schemathesis, 16 do RESTler e 16 do
EvoMaster), o defeito apareceu nas 3 repetições.
As exceções foram:

- NOVO-catwatch-3 pelo Schemathesis: 2/3;
- NOVO-petclinic-rest-8 pelo Schemathesis: 2/3;
- NOVO-petclinic-rest-12 pelo Schemathesis: 1/3.

## i) Defeitos do oráculo não detectados por nenhuma ferramenta

Os 7 defeitos não detectados são todos vulnerabilidades documentadas do VAmPI (`tabelas.md`,
sobreposição; `metricas_por_execucao.csv`). Para saber se as ferramentas chegaram a exercitar
cada vulnerabilidade, foram contadas no tráfego registrado pelo proxy as requisições que a
disparam (`vampi_operacoes_exercitadas.csv`; soma das 3 repetições):

| Defeito | Requisição que a dispara | Schemathesis | RESTler | EvoMaster |
|---|---|---|---|---|
| VAMPI-02 troca de senha de outro usuário | PUT /users/v1/{outro usuário}/password → 204 | 3340 | 0 | 540 |
| VAMPI-03 BOLA em livros | GET /books/v1/{book_title} → 200 | 47197 | 0 | 365 |
| VAMPI-04 mass assignment | POST /users/v1/register com campo `admin` → 200 | 0 | 0 | 355 |
| VAMPI-05 endpoint de debug | GET /users/v1/_debug → 200 | 735 | 9 | 27451 |
| VAMPI-06 enumeração no login | POST /users/v1/login → 400 | 1530 | 381 | 20688 |
| (total de requisições ao VAmPI) | | 454138 | 2730 | 548111 |

**Explicação provável, baseada nessas evidências:**

- **VAMPI-02, VAMPI-04, VAMPI-05 e VAMPI-06.** As ferramentas **enviaram as requisições que
  disparam a vulnerabilidade e receberam respostas de sucesso**, mas não relataram nada.
  Essas falhas não produzem HTTP 500 nem violam a especificação. Uma troca de senha alheia
  devolve 204, o *debug* devolve 200 com dados que a especificação permite e a enumeração
  aparece só no texto da mensagem de erro. Os oráculos das três ferramentas (códigos 5xx,
  conformidade com a especificação e, no RESTler, *checkers* de uso indevido de recursos)
  não têm noção de quem é dono de cada recurso, de quais dados são sensíveis nem de qual
  mensagem é reveladora.

  Uma ressalva sobre VAMPI-04: a contagem considera apenas requisições com o campo `admin`
  no corpo; não foi verificado se o valor enviado era `true`. No VAMPI-03, uma resposta 200
  por si só não prova acesso indevido: seria preciso um segundo usuário, e as ferramentas
  usam um único token (`name1`). Na reprodução manual, o GET do livro de outro usuário com
  o token de `name1` respondeu 404 (`reproducao/manual_vampi.txt`, item 4).
- **VAMPI-08** (falta de *rate limiting*). Nenhuma ferramenta tem oráculo para isso. As
  centenas de milhares de requisições sem nenhuma resposta 429 mostram o problema, mas
  nenhuma ferramenta o relata.
- **VAMPI-09** (chave JWT fraca). Explorar essa falha exige forjar um token assinado com uma
  chave adivinhada. As ferramentas usam o token fornecido e não manipulam a assinatura.

**[interpretação]** Os 7 defeitos não detectados são de **lógica de autorização,
autenticação ou exposição de dados**. Nenhuma das três ferramentas, na configuração padrão,
tem oráculo para essas classes. Os defeitos detectados são falhas que produzem 500, timeout
ou violação do contrato. O recall no VAmPI (16,7% a 33,3%, `tabelas.md`) reflete mais os
limites dos oráculos das ferramentas que a capacidade de exploração delas: todas cobriram
85,7% a 92,9% das operações (`tabelas.md`, Tabela 7).

## j) Falsos positivos e inconclusivos: causas agrupadas

As causas vêm da justificativa de cada relato, aceita pelos avaliadores (`relatos.csv`).
A contagem é em relatos únicos por ferramenta. Um relato emitido por duas ferramentas conta
para as duas, por isso as colunas somam os totais da Tabela 2.

| Classe | Causa | Schemathesis | RESTler | EvoMaster |
|---|---|---|---|---|
| FP | Resposta sem corpo ou sem Content-Type onde a especificação declara um tipo; a API não falhou | 40 | 0 | 0 |
| FP | Content-Type da resposta diferente do documentado (padrão do framework); a API não falhou | 35 | 0 | 6 |
| FP | Código de status correto para a situação, mas não listado na especificação | 30 | 0 | 2 |
| FP | Endpoint interno `/error` do Spring Boot (catwatch), exposto pela especificação gerada automaticamente: chamado diretamente, responde 500 por desenho do framework | 20 | 6 | 13 |
| FP | API rejeita com 400 uma entrada que a especificação não restringe (especificação incompleta) | 13 | 0 | 0 |
| FP | API tolerante: aceita entrada fora do schema e responde normalmente | 5 | 0 | 0 |
| FP | Resposta difere do schema documentado (erro da especificação, não da API) | 3 | 0 | 1 |
| FP | Método não declarado respondido com 400 em vez de 405; a API não falhou | 2 | 0 | 0 |
| FP | Corpo de resposta não documentado na especificação | 0 | 0 | 5 |
| FP | RESTler (InvalidDynamicObjectChecker) anexou `?injected_query_string=123` a um objeto válido e esperava erro; a API ignora o parâmetro e devolve 20x | 0 | 8 | 0 |
| **FP** | **Total** | **148** | **14** | **27** |
| INC | `GET /fetch` (catwatch) depende do GitHub e do mailtrap.io, inacessíveis na rede isolada do experimento (D08); não dá para dizer se o 500 seria um defeito com a rede disponível | 0 | 1 | 2 |
| **INC** | **Total** | **0** | **1** | **2** |

**[interpretação]**

- No Schemathesis, 148 − 20 = 128 dos FP (86%) são **divergências entre a especificação e o
  comportamento correto da API**: tipos de conteúdo, códigos de status e schemas não
  documentados. Os outros 20 são do endpoint `/error`. A precisão baixa do Schemathesis vem
  da sensibilidade dos seus *checks* de conformidade à qualidade da especificação, e não de
  falhas inventadas.
- No RESTler, os FP vêm de um único *checker* e do `/error`.
- O endpoint `/error` gerou FP nas três ferramentas porque aparece na especificação da
  catwatch.

## k) Exemplos concretos (requisição → resposta)

Todos os exemplos foram reproduzidos numa API limpa (`reproducao/<chave>.txt` e
`reproducao/manual_vampi.txt`). O relato de origem de cada um está em `relatos.csv`.

1. **Injeção de SQL no VAmPI (VAMPI-01; RESTler e Schemathesis; relato `3fdc99bcfb2f`).**
   ```
   GET /users/v1/]:X2BCb
   → 500  sqlalchemy.exc.StatementError … [SQL: SELECT * FROM users WHERE username = ']?']
   ```
   O valor do caminho é concatenado no SQL. Na exploração manual, a requisição
   `GET /users/v1/x' UNION SELECT username,password,email,admin,id FROM users--` devolve 200
   com dados da tabela de usuários (`reproducao/manual_vampi.txt`, item 3).

2. **ReDoS no VAmPI (VAMPI-07; só o RESTler; relato `e7f456148913`).**
   ```
   PUT /users/v1/{username}/email   {"email": "<81 caracteres terminando em '!'>"}
   → sem resposta em 30 s (HTTP 000 em 30,03 s)
   ```
   A expressão regular que valida o e-mail entra em retrocesso exponencial
   (`reproducao/manual_vampi.txt`, item 5).

3. **Título de livro de outro usuário (NOVO-vampi-1, chamado de VAMPI-10 no piloto;
   Schemathesis e EvoMaster; relato `3bb5b01b73e9`).**
   ```
   POST /books/v1 (como name1)  {"book_title":"bookTitle12","secret":"x"}   # título de name2
   → 500  sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: books.book_title
   POST /books/v1 (como name1)  {"book_title":"bookTitle72", …}             # título do próprio name1
   → 400  {"status":"fail","message":"Book Already exists!"}
   ```
   A API só verifica duplicidade entre os livros do próprio usuário
   (`reproducao/manual_vampi.txt`, item 1).

4. **Usuário sem papéis no petclinic-rest (NOVO-petclinic-rest-11; as 3 ferramentas; relato
   `f05be19f48b6`).**
   ```
   POST /petclinic/api/users  {"username":"john.doe","password":"oYmcTem0tR","enabled":false}
   → 500  {"title":"IllegalArgumentException","detail":"An unexpected error occurred …"}
   ```
   A regra "todo usuário precisa de um papel" existe no serviço, mas não é traduzida em 400.

5. **Rota inexistente vira 500 (NOVO-petclinic-rest-1; só o RESTler; relato `5c10bb29d699`).**
   ```
   DELETE /petclinic/api/owners/320/?/
   → 500  {"title":"NoResourceFoundException","detail":"An unexpected error occurred …"}
   ```
   O tratador global de exceções do petclinic-rest transforma qualquer exceção, inclusive
   "recurso não encontrado", em 500. Esse é o defeito com mais relatos VP: 39 (`relatos.csv`).

## l) Comparação com o piloto (VAmPI, 10 min, 1 repetição)

Fontes:

- piloto: `piloto/data/results/tabelas.md`, `piloto/data/results/metricas_por_execucao.csv`
  e `piloto/data/ground_truth/oraculo.csv`;
- campanha, só a linha do VAmPI: `tabelas.md`, Tabela 7.

O piloto rodou num GitHub Codespace com 2 vCPUs (`versoes.md`). O oráculo do piloto tinha 10
defeitos: os 9 documentados mais VAMPI-10, que na campanha é **NOVO-vampi-1**. No piloto, as
classificações eram preliminares e foram marcadas como "[PRELIMINAR-IA]" no próprio arquivo
de tabelas.

| Ferramenta | Piloto (10 min, 1 rep.): defeitos detectados | Campanha (30 min, 3 rep.): defeitos detectados (em todas as 3 rep.) |
|---|---|---|
| Schemathesis | VAMPI-01, VAMPI-10 | VAMPI-01, NOVO-vampi-1 (= VAMPI-10), NOVO-vampi-2, NOVO-vampi-3 |
| RESTler | VAMPI-01, VAMPI-07 | VAMPI-01, VAMPI-07 |
| EvoMaster | VAMPI-10 | NOVO-vampi-1 (= VAMPI-10), NOVO-vampi-2 |

| Métrica (VAmPI) | Schemathesis piloto → campanha (média) | RESTler piloto → campanha | EvoMaster piloto → campanha |
|---|---|---|---|
| Requisições | 30379 → 151379 | 918 → 910 | 46546 → 182704 |
| Relatos únicos | 20 → 23.3 | 4 → 4.0 | 9 → 9.3 |
| Precisão | 42.1% → 52.6% | 100.0% → 100.0% | 12.5% → 24.8% |
| Cobertura de operações (%) | 92.9 → 92.9 | 85.7 → 85.7 | 92.9 → 92.9 |
| TTFF (min) | 0.1 → 0.1 | 0.1 → 0.2 | 0.2 → 0.1 |

O recall não é comparável diretamente entre as duas tabelas, porque o oráculo passou de 10
para 12 defeitos. Por isso a comparação é feita pelos defeitos.

**O que se confirmou:**

- os mesmos defeitos documentados foram detectados: VAMPI-01 pelo Schemathesis e pelo
  RESTler, e VAMPI-07 só pelo RESTler;
- o defeito de *pooling* do piloto (VAMPI-10 = NOVO-vampi-1) voltou a aparecer, pelo
  Schemathesis e pelo EvoMaster;
- o RESTler manteve precisão de 100% no VAmPI, com cerca de 900 requisições;
- as ferramentas não detectaram os outros 7 defeitos documentados, nem no piloto nem na
  campanha;
- a cobertura de operações ficou igual.

**O que mudou:**

- com 30 min e 3 repetições, o Schemathesis achou dois defeitos novos (NOVO-vampi-2 e
  NOVO-vampi-3) e o EvoMaster um (NOVO-vampi-2);
- as três ferramentas detectaram os mesmos defeitos em todas as 3 repetições, o que dá
  estabilidade ao resultado do VAmPI;
- o Schemathesis e o EvoMaster fizeram cerca de 4 a 5 vezes mais requisições, com 3× o tempo e
  numa máquina mais rápida;
- a campanha acrescentou duas APIs Java (petclinic-rest e catwatch), em que os recalls
  relativos são bem maiores (Tabela 3).

**[interpretação]** No VAmPI, o resultado do piloto se manteve. O tempo extra trouxe defeitos
de estado, como colisões de título e entradas vazias, mas nenhuma vulnerabilidade de
segurança nova. O fator limitante é o oráculo das ferramentas, e não o orçamento.

## m) Observações para a discussão

Todas as observações desta seção são **[interpretação]**, apoiadas nos números citados.

1. **Recall × precisão.**
   - O Schemathesis teve o maior recall geral: 69,7% dos defeitos na união das repetições e
     68,7% em média (Tabela 3). Também detectou sozinho 6 defeitos (sobreposição: 1 na
     catwatch, 4 no petclinic-rest, 1 no VAmPI).
   - Teve a menor precisão: 45,0% (Tabela 4).
   - O RESTler teve a maior precisão: 88,6% nos relatos únicos e 86,1% em média (Tabelas 4
     e 5). A diferença de precisão entre Schemathesis e RESTler é a única comparação geral
     com p < 0,05 (Â12 = 0,00; p = 0,000).
   - Nas demais métricas gerais (recall, F1, cobertura e DPH), nenhuma diferença foi
     estatisticamente significativa com n = 9.
2. **Pouca potência estatística por API.** Com 3 repetições, o menor p possível fica perto
   de 0,05 a 0,10. Os Â12 extremos (0,00 ou 1,00) na comparação por API mostram diferenças
   consistentes nas 3 repetições, mas não podem ser apresentados como estatisticamente
   significativos.
3. **Complementaridade.** 9 dos 26 defeitos detectados foram achados por uma única
   ferramenta (sobreposição). Exemplos:
   - o RESTler foi o único a detectar o ReDoS (VAMPI-07) e as rotas inexistentes do
     petclinic-rest (NOVO-petclinic-rest-1);
   - o EvoMaster foi o único a detectar a visita com petId inexistente
     (NOVO-petclinic-rest-13);
   - o Schemathesis foi o único a detectar os defeitos de Content-Type e multipart.

   Usar as ferramentas em conjunto aumenta o recall.
4. **O número de requisições não explica a eficácia.**
   - No petclinic-rest, o EvoMaster fez 491.784 requisições em média, cerca de 6 vezes o
     Schemathesis (73.677), e detectou 7 defeitos, contra 10 do Schemathesis (Tabela 7).
   - No VAmPI, o RESTler fez 910 requisições e detectou os mesmos 2 defeitos que o
     EvoMaster com 182.704.
   - Como as execuções são paralelas e os limites de CPU são iguais, as contagens de
     requisições podem variar com a vizinha (A5). Mesmo assim, os mínimos e máximos da
     Tabela 7 são estreitos.
5. **Qualidade da especificação.** A maior parte dos FP vem de divergências entre a
   especificação e o comportamento correto da API (seção j), incluindo o `/error` da
   catwatch. Ferramentas baseadas em conformidade, como o Schemathesis, são mais
   penalizadas por especificações imprecisas.
6. **EvoMaster no petclinic-rest: 100% de precisão por limitação.** O EvoMaster não
   conseguiu interpretar a especificação OpenAPI 3.1 para validar respostas (A3). Por isso
   só relatou HTTP 500, que são VP nessa API.
7. **Recall relativo nas APIs do WFD.** Na catwatch e no petclinic-rest, o oráculo é a
   união do que as ferramentas acharam (D10). Um recall de 100% ali não significa que todos
   os defeitos da API foram encontrados.
8. **Rapidez.** O TTFF ficou em 0,1 a 0,2 min para todas as ferramentas em todas as APIs
   (Tabela 7). As três acham o primeiro defeito real em segundos. Por isso o TTFF não
   diferencia as ferramentas neste estudo.
9. **Ameaças específicas desta campanha:**
   - a revisão foi registrada em bloco, sem medida de concordância entre avaliadores, e a
     classificação partiu de sugestões assistidas por IA (D30, D31, A6);
   - a execução foi paralela (A5);
   - a rede isolada gerou os 3 inconclusivos (D08).

---

*Gerado em 2026-11-24 a partir do commit da Fase 4 do repositório. Scripts:
`analysis/extract_findings.py`, `analysis/reproduzir.py`, `analysis/sugerir.py`,
`analysis/consolidar_revisao.py`, `analysis/compute_metrics.py` e
`analysis/resumir_execucao.py`.*
