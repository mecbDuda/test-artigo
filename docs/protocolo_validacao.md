# Protocolo de validação manual dos relatos

Cada linha de `data/validated/relatos.csv` é um relato único (já deduplicado).
Dois integrantes classificam cada relato **de forma independente** e depois
discutem as divergências.

## Passo a passo para cada relato

1. Suba a API em estado limpo:
   `LOG_DIR=/tmp/val docker compose -p val -f apis/<api>/docker-compose.yml up -d`
   e rode o `INIT_CMD` do `api.env`.
2. Reproduza a requisição da coluna `exemplo` (ou o arquivo de bug do RESTler /
   teste gerado pelo EvoMaster) com `curl` ou Postman.
3. Consulte `data/raw/<execução>/api.log` para ver o *stack trace*, se houver.
4. Classifique:

| Classe | Quando usar |
|---|---|
| `VP` | Reproduz em ambiente limpo **e** é um defeito real. Preencha `defeito_id` com o ID do oráculo. Se for um defeito novo, crie a linha no `oraculo.csv` com `origem=pooling` e use o novo ID. |
| `FP` | Reproduz, mas o comportamento está correto (erro na especificação, 5xx de infraestrutura, resposta válida pelas regras de negócio). Escreva a causa em `observacoes`, pois ela vira a coluna "Principal causa de FP" da Tabela 4. |
| `INC` | Não reproduz de forma determinística ou não há informação para decidir. |

5. Preencha `avaliador_1` e `avaliador_2` com a classificação de cada um
   (ex.: `VP`, `FP`). A coluna `classificacao` recebe a decisão final, após consenso.

## Regras de consistência

- Vários relatos podem apontar para o mesmo `defeito_id`; ele conta **uma vez**
  no recall.
- Um relato que revela dois defeitos recebe os dois IDs separados por `;`.
- Registre no artigo quantas divergências houve entre avaliadores antes do consenso.
- Depois de classificar, rode `python3 analysis/extract_findings.py` de novo
  (as classificações são preservadas) e então `python3 analysis/compute_metrics.py`.
