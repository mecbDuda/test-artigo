# Contexto do projeto

Este arquivo resume o projeto e registra o pedido (prompt) que orientou a campanha completa,
para quem continuar o trabalho, seja uma pessoa ou um assistente de IA. Ele complementa o
`README.md`; os detalhes de método ficam em `docs/`.

## O estudo

Estudo experimental que compara três ferramentas de teste automatizado de APIs REST
(*fuzzers*) quanto à capacidade de encontrar defeitos:

| Ferramenta | Versão | Modo |
|---|---|---|
| Schemathesis | 4.34.0 | baseado na especificação OpenAPI (propriedades/checks) |
| RESTler | 9.2.4 | gramática inferida da especificação, *checkers* de segurança |
| EvoMaster | 5.1.0 | caixa-preta (busca evolutiva) |

APIs alvo (rodando em Docker, numa rede interna sem internet, atrás de um proxy mitmproxy que
registra todo o tráfego em `flows.jsonl`):

| API | Linguagem | Operações | Autenticação | Oráculo |
|---|---|---|---|---|
| VAmPI | Python/Flask | 14 | JWT (usuário `name1`) | 9 vulnerabilidades documentadas (`VAMPI-01` a `VAMPI-09`) |
| petclinic-rest (WFD) | Java 17 / Spring Boot | 43 | nenhuma | sem defeitos documentados; defeitos entram por *pooling* |
| catwatch (WFD) | Java 8 / Spring Boot | 23 | nenhuma | sem defeitos documentados; defeitos entram por *pooling* |

Desenho: 3 ferramentas × 3 APIs × 3 repetições = **27 execuções de 30 minutos**. Cada relato
único é classificado por dois avaliadores como VP (verdadeiro positivo), FP (falso positivo)
ou INC (inconclusivo). Defeitos reais fora do oráculo entram nele com `origem=pooling`.
Métricas: relatos brutos e únicos, VP/FP/INC, recall, precisão, F1, cobertura de operações,
requisições, TTFF (tempo até a primeira falha), DPH (defeitos por hora), sobreposição entre
ferramentas e comparação estatística (Â12 de Vargha-Delaney e teste de Mann-Whitney).

Antes da campanha houve um **estudo piloto** (VAmPI, 10 min, 1 repetição), com dados isolados
em `piloto/` (e na branch `piloto`).

## Onde está cada coisa

| Caminho | Conteúdo |
|---|---|
| `config/experiment.env` | orçamento, repetições, sementes e imagens fixadas por digest |
| `apis/<api>/` | `docker-compose.yml`, especificação OpenAPI e `api.env` de cada API |
| `tools/run_<ferramenta>.sh`, `tools/lib.sh` | como cada ferramenta é executada, com limites de CPU/memória |
| `scripts/run_parallel.py`, `scripts/run_one.sh` | campanha em slots paralelos isolados, com pausa segura (arquivo `PAUSAR`) |
| `scripts/start_background.sh`, `scripts/progress.sh` | iniciar a campanha no tmux e acompanhar o progresso |
| `scripts/commit_dados.sh` | comprime arquivos grandes e faz commit dos dados brutos por partes |
| `data/raw/` | dados brutos das 27 execuções (arquivos > 50 MB versionados como `.gz`) e `recursos.csv` |
| `campaigns.log` | log completo da campanha |
| `analysis/extract_findings.py` | extrai os relatos e gera `data/validated/relatos.csv` e `data/processed/` |
| `analysis/reproduzir.py` | reproduz cada relato numa API limpa (`data/processed/reproducao/`) |
| `analysis/sugerir.py` | sugere VP/FP/INC e defeito para cada relato e gera `docs/guia_revisao.md` |
| `analysis/compute_metrics.py` | calcula as métricas e as tabelas em `data/results/` |
| `data/ground_truth/oraculo.csv` | oráculo de defeitos |
| `docs/desvios.md` | toda mudança em relação ao planejado (D01–D30) e ameaças à validade (A1–A6) |
| `docs/versoes.md` | versões das ferramentas, APIs e máquina usada |
| `docs/protocolo_validacao.md` | protocolo de classificação dos relatos |
| `docs/guia_revisao.md` | guia de revisão dos relatos para os avaliadores |
| `piloto/` | dados e resultados do estudo piloto (não misturar com a campanha) |
| `campanha_codespace/` | 6 execuções de uma primeira tentativa sequencial no Codespace, arquivadas (D21) |

## Situação em 2026-11-24

- **Fases 0 a 2 concluídas.** A campanha rodou num PC com Windows 11 + WSL2 (i5-13400F, 16
  threads, 16 GB de RAM) com **2 slots paralelos**: de 2026-11-23 20:53 a 2026-11-24 18:50,
  com uma pausa segura (00:05 a 14:37). Foram 27/27 execuções concluídas, sem falhas, sem
  execuções refeitas e sem contêiner atingindo o limite de memória.
- **Fase 3 concluída.** A extração deu 1.265 relatos brutos e 390 únicos (vampi 47, catwatch 75,
  petclinic-rest 268). Cada relato foi reproduzido numa API limpa (359 reproduziram) e recebeu
  uma sugestão: 206 VP, 182 FP e 2 INC, com 3 defeitos novos no VAmPI, 8 na catwatch e 13 no
  petclinic-rest.
- **Em andamento: revisão pela equipe.** Os dois avaliadores marcam "ok" ou a classificação
  correta, por uma página de revisão compartilhada (as marcações são depois copiadas para as
  colunas `avaliador_1` e `avaliador_2` de `data/validated/relatos.csv`) ou diretamente no CSV.
  As colunas `classificacao` e `defeito_id` só são preenchidas na Fase 4.
- **Próximos passos:** Fase 4 (consolidar a revisão, decidir divergências, atualizar o
  oráculo, calcular as métricas), Fase 5 (`RESULTADOS_PARA_ARTIGO.md`) e Fase 6 (organizar o
  repositório e reescrever o README para a professora).

## Ferramentas de apoio

A execução da campanha, a reprodução dos relatos e as sugestões de classificação foram
automatizadas com apoio de um assistente de IA. As
sugestões são revisadas por dois membros da equipe, e a decisão final é deles (`docs/desvios.md`,
D30).

## Pedido que orientou a campanha (prompt)

Texto enviado ao assistente de IA no início da campanha completa, reproduzido sem alterações:

```text
Neste computador quero executar a CAMPANHA COMPLETA do estudo, com execuções em
paralelo, e gerar UM ÚNICO arquivo Markdown com todos os resultados, que vou
entregar a outra pessoa para escrever o artigo. A campanha vai rodar durante a
noite; o tempo total pode chegar a 9 horas. O computador tem 16 GB de RAM e
talvez precise ser desligado no meio, por isso a execução precisa poder pausar
e retomar.

REGRAS INEGOCIÁVEIS
- Nunca invente, altere ou "corrija" dados coletados. Todo número do relatório
  deve vir de data/results/ ou data/processed/.
- Os dados do piloto ficam em piloto/ e não se misturam aos da campanha.
- Toda mudança em relação ao planejado vai para docs/desvios.md.
- Só me interrompa em bloqueios ou nos pontos marcados com "PARE".

FASE 0 – REPOSITÓRIO E AMBIENTE
1. Confirme que esta pasta é um clone de https://github.com/mecbduda/test-artigo
   na branch main, atualizado (git pull).
2. Leia README.md e docs/ (desvios.md, versoes.md, protocolo_validacao.md).
3. Verifique: SO (Linux ou WSL2), nproc, memória livre, disco livre, Docker
   (docker run hello-world), Compose v2, Python 3 com pyyaml e scipy, tmux.
   Instale o que faltar. Teste se --network host funciona (suba algo
   escutando numa porta e acesse com
   docker run --rm --network host alpine wget -qO- http://localhost:<porta>).
   Se não funcionar, adapte os scripts para uma rede Docker compartilhada e
   registre a mudança.
4. Na main, confirme que data/raw/, data/processed/, data/results/ e
   data/validated/relatos.csv estão vazios ou inexistentes e que o oraculo.csv
   não tem a linha VAMPI-10. Faça pull de todas as imagens (versões fixadas em
   config/experiment.env).
5. Registre a máquina em docs/versoes.md (seção "Campanha completa").

FASE 1 – PARALELIZAÇÃO E PAUSA SEGURA
6. Hoje os scripts assumem uma execução por vez: porta fixa do proxy (8080),
   porta fixa do servidor da especificação (8099), projeto compose fixo e
   nomes de contêiner fixos. Adapte para N execuções simultâneas isoladas:
   - cada slot usa portas próprias (proxy 8080+k, especificação 8099+k),
     projeto compose próprio (fuzzexp_k) e nomes de contêiner com sufixo único;
   - BASE_URL, SCHEMA_URL, HEALTH_URL, INIT_CMD e os scripts de autenticação
     passam a usar as portas do slot;
   - cada contêiner (API, proxy e ferramenta) recebe limites de CPU e memória
     IGUAIS para todas as ferramentas (--cpus e --memory no docker run e
     limites no compose), calculados a partir de nproc e da RAM, deixando
     ~2 GB livres para o sistema;
   - crie scripts/run_parallel.sh (ou .py) que distribui a fila de execuções
     entre os slots, intercalando ferramentas e APIs para que nenhuma
     ferramenta rode sempre com os mesmos vizinhos, pula execuções já
     concluídas e grava em meta.json o slot e as execuções vizinhas.
7. Pausa segura: se existir o arquivo PAUSAR na raiz do repositório, o
   run_parallel não inicia novas execuções, espera as que estão rodando
   terminarem e encerra, imprimindo "PAUSADO COM SEGURANÇA – pode desligar".
   Ao iniciar, o script sempre detecta execuções incompletas (pasta sem
   meta.json), move-as para data/raw/_incompletas/ e as refaz. Cada pausa e
   cada execução refeita é registrada em docs/desvios.md.
8. Orçamento e paralelismo: 27 execuções (3 ferramentas × 3 APIs
   vampi/petclinic-rest/catwatch × 3 repetições) com 30 min por execução,
   conforme a metodologia planejada. Use 2 slots paralelos (duração estimada
   ~7,5 h). Use 3 slots só se a RAM medida no teste rápido permitir com folga
   e a estimativa com 2 slots passar de 9 h. Não reduza o orçamento nem as
   repetições. Registre a decisão e o cálculo em docs/desvios.md.
9. Teste rápido em paralelo: BUDGET_MIN=2, REPS=1, as 3 APIs, todos os slots.
   Para cada ferramenta × API confirme: requisições em flows.jsonl (e só do
   próprio slot), logs sem erro, achados extraídos, nenhuma interferência
   entre slots e memória dentro do limite (docker stats). Teste também a
   pausa segura (crie PAUSAR no meio do teste e confirme que ela funciona).
   Corrija o que for preciso, apague as saídas do teste e faça commit e push
   das mudanças de código.

FASE 2 – CAMPANHA
10. Rode scripts/run_parallel.sh dentro do tmux, com saída em campaigns.log,
    registrando o uso de CPU e memória a cada minuto em data/raw/recursos.csv.
    Me explique: como acompanhar o progresso, como pausar com segurança
    (touch PAUSAR) e como retomar depois de ligar o computador de novo.
11. Ao terminar, faça commit e push de campaigns.log, recursos.csv e data/raw/
    (comprima arquivos > 50 MB; os que passarem de 100 MB ficam fora do
    commit, com anotação em docs/desvios.md).

FASE 3 – PREPARAR A REVISÃO DA EQUIPE
12. Rode analysis/extract_findings.py. Para cada relato de
    data/validated/relatos.csv, analise as evidências (curl, stack trace no
    api.log, relatório da ferramenta) e, sempre que possível, REPRODUZA a
    requisição com a API em estado limpo. Adicione as colunas "sugestao"
    (VP/FP/INC), "defeito_sugerido" (ID do oráculo, ou NOVO-<api>-n para
    defeito real fora do oráculo), "justificativa" e "reproduzido" (sim/não).
    Deixe "classificacao", "defeito_id", "avaliador_1" e "avaliador_2" VAZIAS.
13. Crie docs/guia_revisao.md agrupando os relatos por API e por defeito
    sugerido, com a evidência resumida de cada um. No topo, explique: cada
    avaliador escreve "ok" na sua coluna se concorda com a sugestão, ou a
    classificação que considera certa.
14. Commit e push. Me diga quantos relatos há por API e por ferramenta.
    PARE e espere eu dizer "revisão concluída".

FASE 4 – FECHAR OS DADOS (após "revisão concluída")
15. Onde os dois avaliadores marcaram "ok", classificacao = sugestao. Liste os
    casos com discordância e PARE para eu decidir. Conte as divergências.
16. Inclua no oraculo.csv, com origem=pooling, os defeitos novos confirmados.
    Rode extract_findings.py e compute_metrics.py. Commit e push.

FASE 5 – RELATÓRIO ÚNICO
17. Crie RESULTADOS_PARA_ARTIGO.md na raiz, autocontido (quem ler não terá
    acesso ao repositório), com:
    a) Configuração executada: ferramentas e versões, APIs, repetições,
       orçamento, nº de slots paralelos, limites de CPU/memória por contêiner,
       máquina (CPU, núcleos, RAM, SO), datas, duração total, pausas,
       execuções concluídas, refeitas e falhas.
    b) Desvios em relação ao planejado (resumo de docs/desvios.md), incluindo
       a paralelização e seus possíveis efeitos, e problemas ocorridos.
    c) Uso de recursos: pico e média de CPU e memória (de recursos.csv) e se
       algum contêiner atingiu o limite.
    d) Caracterização das APIs: linguagem, nº de operações, autenticação,
       tamanho final do oráculo (documentados + pooling).
    e) Oráculo final: tabela com ID, API, operação, tipo, origem, descrição.
    f) Como foi feita a classificação: sugestões com evidência, quantos
       relatos foram reproduzidos, revisão por dois avaliadores, nº de
       divergências e como foram resolvidas.
    g) Todas as tabelas de data/results/tabelas.md, por ferramenta e por API,
       com média e mínimo–máximo entre as repetições: relatos brutos, únicos,
       VP, FP e INC, recall, precisão, F1, cobertura de operações,
       requisições, TTFF, DPH, sobreposição de defeitos entre ferramentas e
       comparação estatística (Â12 e p de Mann-Whitney).
    h) Defeitos detectados: descrição, ferramentas que o detectaram e em
       quantas das 3 repetições.
    i) Defeitos do oráculo não detectados por nenhuma ferramenta, com a
       explicação provável baseada nas evidências.
    j) Falsos positivos e inconclusivos: causas agrupadas, com contagem por
       ferramenta.
    k) 3 a 5 exemplos concretos e curtos (requisição → resposta) dos achados
       mais interessantes.
    l) Comparação com o piloto (VAmPI, 10 min, 1 repetição; dados em piloto/):
       o que se confirmou e o que mudou com mais tempo e mais repetições.
    m) Observações relevantes para a discussão, marcadas como "interpretação"
       para separá-las dos fatos.
    Para cada número, indique entre parênteses o arquivo de origem.

FASE 6 – ORGANIZAR O REPOSITÓRIO PARA ENTREGA
18. Apague arquivos temporários, saídas de testes, caches e arquivos não
    usados; atualize o .gitignore; confira se a estrutura bate com o README;
    apague branches remotas não usadas (exceto main e piloto).
19. Reescreva o README.md para a professora: objetivo, equipe, estrutura de
    pastas, como reproduzir (inclusive o modo paralelo e a pausa), onde estão
    os dados brutos, validados e resultados, resumo dos principais resultados
    com link para RESULTADOS_PARA_ARTIGO.md e uma seção "Ferramentas
    utilizadas" (ferramentas de teste, APIs alvo, bibliotecas e o assistente
    de IA usado para automatizar a execução e sugerir classificações revisadas
    pela equipe).
20. Garanta que nenhum arquivo contém credenciais, tokens ou caminhos
    pessoais e que todo script tem um comentário no topo dizendo o que faz.
    Commit e push ("Organiza repositório para entrega") e me mostre o caminho
    do RESULTADOS_PARA_ARTIGO.md.
```

### Instruções dadas depois, durante o trabalho

- Arquivar as 6 execuções da primeira tentativa no Codespace e refazê-las nesta máquina (D21).
- Pausar a campanha com segurança para desligar o computador e retomá-la depois (registrado em `docs/desvios.md`).
- Colocar as sugestões de classificação numa forma prática para a equipe validar (página de revisão compartilhada).
- Criar este arquivo `CONTEXTO.md` com o contexto do projeto e o prompt.
