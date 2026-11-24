# Avaliação comparativa de ferramentas de fuzz testing em APIs REST

Artefatos de pesquisa do artigo *"Avaliação comparativa de ferramentas de fuzz testing na
detecção de falhas em APIs REST: um estudo empírico baseado em benchmark"*.

**Equipe:** Maria Eduarda Braga, Letícia Uchôa, Lorena Castello Branco, Gabriela Brito, Rinaldo da Silva.

## Objetivo

O estudo compara três ferramentas de teste automatizado de APIs REST (*fuzzers*):
**Schemathesis**, **RESTler** e **EvoMaster** (modo caixa-preta). O objetivo é medir a
capacidade de cada uma de encontrar defeitos (recall, precisão e F1), além da exploração e do
custo (cobertura de operações, requisições, tempo até a primeira falha e defeitos por hora).

As ferramentas foram testadas em três APIs: **VAmPI**, **petclinic-rest** e **catwatch**. O
desenho tem 3 repetições de 30 minutos por par ferramenta × API, num total de **27
execuções**.

> **Todos os resultados estão em [`RESULTADOS_PARA_ARTIGO.md`](RESULTADOS_PARA_ARTIGO.md)**,
> documento autocontido que indica o arquivo de origem de cada número.

## Resumo dos principais resultados

Fontes: `data/results/tabelas.md` e `data/ground_truth/oraculo.csv`.

- **Campanha.** As 27 execuções foram concluídas, sem falhas e sem execuções refeitas, em
  2 slots paralelos com limites de CPU e memória iguais para todas as ferramentas. Nenhum
  contêiner atingiu o limite de memória.
- **Relatos.** Foram 390 relatos únicos, classificados como 206 VP, 182 FP e 2 INC.
- **Oráculo.** Tem 33 defeitos: as 9 vulnerabilidades documentadas do VAmPI e 24 defeitos
  novos confirmados por *pooling* (3 no VAmPI, 8 na catwatch e 13 no petclinic-rest).

| Ferramenta | Defeitos detectados (de 33) | Recall médio | Precisão (relatos únicos) | F1 médio |
|---|---|---|---|---|
| Schemathesis | 23 | 68.7% | 45.0% | 0.47 |
| RESTler | 16 | 52.7% | 88.6% | 0.57 |
| EvoMaster (caixa-preta) | 16 | 52.7% | 55.0% | 0.48 |

Principais observações:

- O Schemathesis encontrou mais defeitos. A maior parte dos seus falsos positivos vem de
  divergências entre a especificação e o comportamento correto da API.
- O RESTler foi o mais preciso. A diferença de precisão entre RESTler e Schemathesis foi a
  única diferença estatisticamente significativa no geral (Mann-Whitney, p < 0,001).
- As ferramentas se complementam: 9 dos 26 defeitos detectados foram achados por uma única
  ferramenta.
- Nenhuma ferramenta detectou 7 das 9 vulnerabilidades documentadas do VAmPI (autorização,
  autenticação, exposição de dados e *rate limiting*). As ferramentas exercitaram essas
  operações, mas não têm oráculo para reconhecer essas falhas.

## Como o experimento funciona

```
 ferramenta ──HTTP──▶ proxy (mitmproxy, porta 8080+k) ──▶ API alvo (contêiner, rede interna sem internet)
                         │
                         └─▶ data/raw/<execução>/flows.jsonl  (todas as requisições e respostas)
```

As três ferramentas acessam a API **pelo mesmo proxy**. Assim, as requisições, as operações
cobertas, as respostas 5xx e o tempo de cada evento são medidos do mesmo jeito para todas,
seja qual for o formato de relatório de cada ferramenta.

A cada execução, a API é recriada com o estado inicial. A campanha roda em *k* **slots
paralelos isolados**: cada slot tem portas próprias, projeto Docker Compose e redes próprias,
e limites de CPU e memória por contêiner.

## Estrutura de pastas

| Caminho | Conteúdo |
|---|---|
| `RESULTADOS_PARA_ARTIGO.md` | **relatório final com todos os resultados** |
| `CONTEXTO.md` | contexto do projeto e o pedido que orientou a campanha completa |
| `config/experiment.env` | parâmetros do experimento: ferramentas, APIs, repetições, orçamento, semente e imagens fixadas por digest |
| `apis/<api>/` | `docker-compose.yml` (API + proxy), `api.env`, especificação OpenAPI e, no VAmPI, script de autenticação; `apis/_template/` explica como adicionar outra API |
| `proxy/log_flows.py` | addon do mitmproxy que registra as requisições |
| `tools/run_*.sh`, `tools/lib.sh` | *wrappers* que executam cada ferramenta com o orçamento de tempo e os limites de CPU e memória |
| `scripts/run_parallel.py` | executa a campanha em slots paralelos, com pausa segura e retomada |
| `scripts/run_one.sh` | executa uma única execução (API × ferramenta × repetição) num slot |
| `scripts/start_background.sh` | inicia ou retoma a campanha numa sessão tmux |
| `scripts/run_campaigns.sh` | executa a campanha em primeiro plano (atalho para `run_parallel.py`) |
| `scripts/progress.sh` | mostra o progresso da campanha |
| `scripts/limites.sh` | calcula os limites de CPU e memória por contêiner |
| `scripts/commit_dados.sh` | comprime arquivos grandes e faz o commit dos dados brutos |
| `analysis/extract_findings.py` | extrai e deduplica os achados e gera `data/processed/` e `data/validated/relatos.csv` |
| `analysis/reproduzir.py` | reproduz cada relato numa API limpa e grava a evidência em `data/processed/reproducao/` |
| `analysis/sugerir.py` | sugere VP/FP/INC e o defeito de cada relato e gera `docs/guia_revisao.md` |
| `analysis/consolidar_revisao.py` | consolida a revisão dos avaliadores e acrescenta ao oráculo os defeitos de *pooling* |
| `analysis/compute_metrics.py` | calcula as métricas e as tabelas em `data/results/` |
| `analysis/resumir_execucao.py` | resume datas, uso de recursos e operações exercitadas, em `data/processed/` |
| `campaigns.log` | log completo da campanha |
| `docs/desvios.md` | **todas as mudanças em relação ao planejado (D01–D31) e ameaças à validade (A1–A6)** |
| `docs/versoes.md` | versões das ferramentas e APIs e a máquina usada |
| `docs/protocolo_validacao.md` | protocolo de classificação dos relatos |
| `docs/guia_revisao.md` | relatos agrupados por API e defeito, com a evidência resumida, para a revisão |
| `docs/passagem.md` | relatório de passagem da fase de preparação (histórico) |
| `piloto/` | dados e resultados do **estudo piloto** (VAmPI, 10 min, 1 repetição), separados da campanha |
| `campanha_codespace/` | 6 execuções de uma primeira tentativa sequencial, arquivadas e **fora da análise** (`docs/desvios.md`, D21) |

## Onde estão os dados

| Tipo | Local | Observação |
|---|---|---|
| **Brutos** | `data/raw/<api>__<ferramenta>__rep<n>/` | Uma pasta por execução, com `meta.json` (configuração, slot e vizinhas), `flows.jsonl` (tráfego), `api.log`, relatórios e logs da ferramenta e `conteineres.tsv` (pico de memória e OOM). Ficam ainda `data/raw/recursos.csv` (CPU e memória a cada minuto) e `campaigns.log`. **Nunca editados.** Os arquivos acima de 50 MB estão versionados comprimidos (`.gz`). |
| **Processados** | `data/processed/` | Achados por execução, estatísticas de exploração, evidência de reprodução de cada relato (`reproducao/`) e resumos de execução e recursos. |
| **Validados** | `data/validated/relatos.csv` | Os 390 relatos únicos, com sugestão, justificativa, reprodução, marcações dos dois avaliadores e classificação final. |
| **Oráculo** | `data/ground_truth/oraculo.csv` | 33 defeitos: 9 documentados e 24 de *pooling*. |
| **Resultados** | `data/results/` | `tabelas.md` e um CSV por tabela, com métricas por execução, comparação estatística e sobreposição. |

## Como reproduzir

### Pré-requisitos

- Linux ou WSL2 no Windows. A campanha rodou em WSL2 (Ubuntu 24.04) com Docker Engine nativo
  (`docs/versoes.md`). Os contêineres das ferramentas usam `--network host`, que não funciona
  no Docker Desktop do macOS.
- Docker e Docker Compose v2, `curl` e `tmux`.
- Python 3.9+ com `pyyaml` e `scipy` (`pip install pyyaml scipy`).
- Cerca de 16 GB de RAM para 2 slots e uns 20 GB de disco para os dados brutos.

### 1. Baixar as imagens

São as mesmas referências fixadas em `config/experiment.env` e `apis/*/docker-compose.yml`:

```bash
docker pull erev0s/vampi:latest@sha256:0a5a224b6e14ae7da6a6ea265178ff71286ff903aec74adee98f660bb0e4ca12
docker pull mitmproxy/mitmproxy:10.3.0@sha256:a22a4f2178ac5876598402c7060868ec96e90710b31e768ed25a57f501d9f48d
docker pull schemathesis/schemathesis:4.34.0@sha256:7aa27b2085e944c81f5225c52c29bf072778bb5d59e6b27e1876b4757e266a14
docker pull mcr.microsoft.com/restlerfuzzer/restler:v9.2.4@sha256:f37705fc4a11071f1de67ac4708fd97c71c1b4e5a0bc0f9c16c21028c0c41cbb
docker pull webfuzzing/evomaster:v5.1.0@sha256:cf02675504a0b51c268c9320e7d6f7fce92e038c62d5a0bdb25e175ea86c0c89
docker pull webfuzzing/wfd-petclinic-rest:FINAL@sha256:ea7d5dcc6d0144479c8636ab0b0cc1125f29e30b5e9f0c08e64e6e820ed1a70f
docker pull webfuzzing/wfd-catwatch:FINAL@sha256:814cfa76226f4e0f2adb01aa4eba95bc296971a25ac20a33be597b1fd1d68ef2
```

### 2. Teste rápido em paralelo

```bash
SLOTS=2 BUDGET_MIN=2 REPS=1 python3 scripts/run_parallel.py
python3 analysis/extract_findings.py
```

Confira se cada `data/raw/*/flows.jsonl` tem requisições e se as três ferramentas aparecem em
`data/processed/achados_por_execucao.csv`. Depois apague a saída do teste:

```bash
rm -rf data/raw/* data/processed data/validated/relatos.csv
```

### 3. Campanha completa: modo paralelo, pausa e retomada

```bash
./scripts/start_background.sh     # inicia numa sessão tmux; SLOTS=2 por padrão
./scripts/progress.sh             # execuções concluídas, em andamento, estimativa
tmux attach -t campanhas          # acompanhar ao vivo (sair sem parar: Ctrl+b, depois d)
```

- **Paralelismo.** O número de slots vem da variável `SLOTS`. Os limites de CPU e memória
  por contêiner são calculados por `scripts/limites.sh` a partir de `nproc` e da RAM,
  reservando 2 GB e 2 CPUs para o sistema. Com 2 slots, a campanha levou 7,4 h de execução.
- **Pausa segura.** Com `touch PAUSAR` na raiz do repositório, nenhuma execução nova é
  iniciada. As que estão rodando terminam, e o script encerra com "PAUSADO COM SEGURANÇA –
  pode desligar".
- **Retomada.** Rode `./scripts/start_background.sh` de novo. Ele apaga `PAUSAR` e pula as
  execuções concluídas (com `meta.json`). As execuções interrompidas por um desligamento
  brusco vão para `data/raw/_incompletas/` e são refeitas.
- **No WSL.** Mantenha um terminal do Ubuntu aberto, porque a distribuição desliga quando
  nenhum processo do Windows a mantém ativa.

### 4. Análise

```bash
python3 analysis/extract_findings.py     # relatos únicos → data/validated/relatos.csv
python3 analysis/reproduzir.py           # reproduz cada relato numa API limpa (sobe os contêineres)
python3 analysis/sugerir.py              # sugestões e docs/guia_revisao.md
# os dois avaliadores preenchem avaliador_1 e avaliador_2 em data/validated/relatos.csv
python3 analysis/consolidar_revisao.py   # classificação final, divergências e oráculo (pooling)
python3 analysis/extract_findings.py     # de novo: preserva as colunas de classificação
python3 analysis/compute_metrics.py      # métricas → data/results/tabelas.md
python3 analysis/resumir_execucao.py     # resumos de execução e recursos
```

Para reanalisar a partir de um clone, descomprima antes os dados brutos (cerca de 15 GB):

```bash
find data/raw -name '*.gz' -exec gunzip -k {} +
```

### Definição das métricas

| Métrica | Definição |
|---|---|
| Recall | defeitos do oráculo detectados ÷ defeitos do oráculo da API |
| Precisão | relatos VP ÷ (relatos VP + relatos FP), em relatos únicos; os INC ficam fora |
| F1 | 2·P·R / (P + R) |
| Cobertura de operações | operações da especificação com pelo menos uma resposta 2xx ÷ total de operações |
| TTFF | minutos até o primeiro achado classificado como VP |
| DPH | defeitos distintos confirmados ÷ horas de orçamento |
| Â12 e p | tamanho de efeito de Vargha-Delaney e teste de Mann-Whitney bilateral entre pares de ferramentas |

## Ferramentas utilizadas

**Ferramentas de teste comparadas**

- [Schemathesis](https://github.com/schemathesis/schemathesis) 4.34.0: testes baseados em
  propriedades a partir da especificação OpenAPI.
- [RESTler](https://github.com/microsoft/restler-fuzzer) v9.2.4 (Microsoft): *fuzzing*
  stateful por gramática inferida da especificação.
- [EvoMaster](https://github.com/WebFuzzing/EvoMaster) 5.1.0, em modo caixa-preta: geração de
  testes por busca evolutiva.

**APIs alvo**

- [VAmPI](https://github.com/erev0s/VAmPI): API Flask deliberadamente vulnerável, com 14
  operações.
- [petclinic-rest](https://github.com/spring-petclinic/spring-petclinic-rest), com 43
  operações, e catwatch, com 23 operações: as duas são APIs Spring Boot do benchmark
  [Web Fuzzing Dataset (WFD)](https://github.com/WebFuzzing/Dataset).

**Infraestrutura e bibliotecas**

- Docker Engine e Docker Compose v2, para isolar as APIs e as ferramentas e aplicar os
  limites de CPU e memória.
- [mitmproxy](https://mitmproxy.org/) 10.3.0, proxy reverso que registra o tráfego.
- tmux, para a execução em segundo plano.
- Python 3, com [PyYAML](https://pyyaml.org/), para ler as especificações, e
  [SciPy](https://scipy.org/), para o teste de Mann-Whitney.

**Assistente de IA**

- Um assistente de IA foi usado para automatizar:
  - a preparação e a execução da campanha (paralelização, pausa segura, coleta de recursos);
  - a reprodução dos relatos;
  - as **sugestões de classificação** (VP/FP/INC e defeito), com regras explícitas em
    `analysis/sugerir.py`;
  - a redação de `RESULTADOS_PARA_ARTIGO.md`.

  As sugestões foram revisadas por dois membros da equipe, e a decisão final é deles
  (`docs/desvios.md`, D30 e D31; ameaça A6).

## Observações sobre os dados

Os dados brutos (`data/raw/`, `campanha_codespace/`) contêm tokens JWT e senhas de exemplo do
VAmPI (`pass1`, …). Eles pertencem às instâncias locais e descartáveis da API, criadas a cada
execução, e não são credenciais reais. Os tokens estão expirados. Esses arquivos são
preservados como foram coletados. Nas evidências processadas, os tokens foram removidos.

## Licença

Scripts sob licença MIT. As APIs alvo e as ferramentas mantêm suas próprias licenças.
