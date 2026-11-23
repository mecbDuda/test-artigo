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
```bash
# especificação do VAmPI
curl -L -o apis/vampi/openapi3.yml \
  https://raw.githubusercontent.com/erev0s/VAmPI/master/openapi_specs/openapi3.yml

# baixar as imagens
docker pull erev0s/vampi:latest
docker pull mitmproxy/mitmproxy:10.3.0
docker pull schemathesis/schemathesis:stable
docker pull mcr.microsoft.com/restlerfuzzer/restler:v8.5.0
docker pull webfuzzing/evomaster:v5.1.0
```
Fixe as versões em `config/experiment.env` e registre-as no artigo (Quadro 3).
Para adicionar outras APIs, siga `apis/_template/README.md`.

### 2. Teste rápido (obrigatório antes das campanhas reais)
```bash
BUDGET_MIN=2 REPS=1 ./scripts/run_campaigns.sh
python3 analysis/extract_findings.py
```
Confira, para **cada ferramenta**, se:
- `data/raw/vampi__<ferramenta>__rep1/flows.jsonl` tem requisições (a ferramenta passou pelo proxy);
- `tool_stdout_*.log` não mostra erro de parâmetro (as opções de CLI mudam entre versões; veja os comentários no topo de cada `tools/run_*.sh`);
- os achados próprios da ferramenta (violações de esquema no Schemathesis, checkers no RESTler) aparecem em `data/processed/achados_por_execucao.csv`.

Depois apague o teste: `rm -rf data/raw/* data/processed data/validated/relatos.csv`.

### 3. Campanhas reais
```bash
./scripts/run_campaigns.sh      # ex.: 3 ferramentas × 3 APIs × 3 repetições × 30 min ≈ 13,5 h
```
Execuções já concluídas são puladas; dá para interromper e continuar depois.

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
