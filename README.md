# Avaliação comparativa de ferramentas de fuzz testing em APIs REST

Artefatos de pesquisa do artigo *"Avaliação comparativa de ferramentas de fuzz
testing na detecção de falhas em APIs REST: um estudo empírico baseado em benchmark"*.

Equipe: Maria Eduarda Braga, Letícia Uchôa, Lorena Castello Branco, Gabriela Brito, Rinaldo da Silva.

Ferramentas comparadas: **Schemathesis**, **RESTler** e **EvoMaster (caixa-preta)**.

## Como o experimento funciona

```
 ferramenta ──HTTP──▶ proxy (mitmproxy, :8080) ──▶ API alvo (contêiner)
                         │
                         └─▶ data/raw/<execução>/flows.jsonl  (todas as requisições/respostas)
```

As três ferramentas acessam a API **pelo mesmo proxy**. Assim, número de
requisições, operações cobertas, respostas 5xx e tempo de cada evento são medidos
do mesmo jeito para todas, independentemente do formato de relatório de cada uma.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `config/experiment.env` | parâmetros do experimento (ferramentas, APIs, repetições, orçamento, versões) |
| `apis/<api>/` | `docker-compose.yml` (API + proxy), `api.env`, especificação OpenAPI, script de autenticação |
| `proxy/log_flows.py` | addon do mitmproxy que registra as requisições |
| `tools/run_*.sh` | wrappers que executam cada ferramenta com o orçamento de tempo |
| `scripts/run_campaigns.sh` | executa todas as campanhas com reset de estado entre elas |
| `analysis/extract_findings.py` | extrai e deduplica os achados → `data/validated/relatos.csv` |
| `analysis/compute_metrics.py` | calcula precisão, recall, F1, cobertura, TTFF, DPH → `data/results/` |
| `data/ground_truth/oraculo.csv` | oráculo de defeitos conhecidos |
| `data/raw/` | saídas brutas de cada execução (logs, relatórios das ferramentas) |
| `data/validated/relatos.csv` | relatos classificados manualmente (VP/FP/INC) |
| `data/results/` | tabelas finais usadas no artigo |
| `docs/protocolo_validacao.md` | como classificar os relatos |

## Pré-requisitos

- Linux (ou WSL2 no Windows). Os contêineres usam `--network host`, que não funciona no Docker Desktop do macOS.
- Docker + Docker Compose v2, `curl`, Python 3.9+ com `pyyaml` (`pip install pyyaml`; `scipy` é opcional, para o teste de Mann-Whitney).
- Espaço para as imagens: Schemathesis, RESTler, EvoMaster, mitmproxy e as APIs.

## Passo a passo

### 1. Preparar
As especificações já estão no repositório (`apis/*/openapi*`). As imagens são
fixadas por digest em `config/experiment.env` e `apis/*/docker-compose.yml`
(versões e máquina em `docs/versoes.md`; mudanças de método em `docs/desvios.md`).
```bash
# baixar as imagens (mesmas referências fixadas nos arquivos de configuração)
docker pull erev0s/vampi:latest@sha256:0a5a224b6e14ae7da6a6ea265178ff71286ff903aec74adee98f660bb0e4ca12
docker pull mitmproxy/mitmproxy:10.3.0@sha256:a22a4f2178ac5876598402c7060868ec96e90710b31e768ed25a57f501d9f48d
docker pull schemathesis/schemathesis:4.34.0@sha256:7aa27b2085e944c81f5225c52c29bf072778bb5d59e6b27e1876b4757e266a14
docker pull mcr.microsoft.com/restlerfuzzer/restler:v9.2.4@sha256:f37705fc4a11071f1de67ac4708fd97c71c1b4e5a0bc0f9c16c21028c0c41cbb
docker pull webfuzzing/evomaster:v5.1.0@sha256:cf02675504a0b51c268c9320e7d6f7fce92e038c62d5a0bdb25e175ea86c0c89
docker pull webfuzzing/wfd-petclinic-rest:FINAL@sha256:ea7d5dcc6d0144479c8636ab0b0cc1125f29e30b5e9f0c08e64e6e820ed1a70f
docker pull webfuzzing/wfd-catwatch:FINAL@sha256:814cfa76226f4e0f2adb01aa4eba95bc296971a25ac20a33be597b1fd1d68ef2
```
APIs: `vampi`, `petclinic-rest` e `catwatch` (as duas últimas do Web Fuzzing Dataset).
Para adicionar outras APIs, siga `apis/_template/README.md`.

### 2. Teste rápido (obrigatório antes das campanhas reais)
```bash
BUDGET_MIN=2 REPS=1 APIS="vampi petclinic-rest catwatch" ./scripts/run_campaigns.sh
python3 analysis/extract_findings.py
```
Confira, para **cada ferramenta**, se:
- `data/raw/vampi__<ferramenta>__rep1/flows.jsonl` tem requisições (a ferramenta passou pelo proxy);
- `tool_stdout_*.log` não mostra erro de parâmetro (as opções de CLI mudam entre versões; veja os comentários no topo de cada `tools/run_*.sh`);
- os achados próprios da ferramenta (violações de esquema no Schemathesis, checkers no RESTler) aparecem em `data/processed/achados_por_execucao.csv`.

Depois apague o teste: `rm -rf data/raw/* data/processed data/validated/relatos.csv`.

### 3. Campanhas reais
```bash
./scripts/start_background.sh   # 3 ferramentas × 3 APIs × 3 repetições × 30 min ≈ 14,5 h com preparação
./scripts/progress.sh           # progresso; ao vivo: tmux attach -t campanhas  ou  tail -f campaigns.log
```
Execuções já concluídas (com `meta.json`) são puladas. Execuções interrompidas
são movidas para `data/raw/_incompletas/` e refeitas. Para retomar, rode
`./scripts/start_background.sh` de novo.

### 4. Extração e validação manual
```bash
python3 analysis/extract_findings.py
```
Classifique cada linha de `data/validated/relatos.csv` seguindo `docs/protocolo_validacao.md`.
Defeitos reais novos entram no `oraculo.csv` com `origem=pooling`.

### 5. Métricas
```bash
python3 analysis/extract_findings.py   # de novo, preserva as classificações
python3 analysis/compute_metrics.py
```
As Tabelas 2 a 6 do artigo ficam em `data/results/tabelas.md` (e em CSV).

## Definição das métricas

| Métrica | Definição |
|---|---|
| Recall | defeitos do oráculo detectados ÷ defeitos do oráculo da API |
| Precisão | relatos VP ÷ (relatos VP + relatos FP), em relatos únicos; INC fica fora |
| F1 | 2·P·R / (P + R) |
| Cobertura de operações | operações da especificação com ao menos uma resposta 2xx ÷ total de operações |
| TTFF | minutos até o primeiro achado classificado como VP |
| DPH | defeitos distintos confirmados ÷ horas de orçamento |

## Licença

Scripts sob licença MIT. As APIs alvo e as ferramentas mantêm suas próprias licenças.
