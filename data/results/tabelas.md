# Tabelas geradas automaticamente

Execuções consideradas: 3. Valores de média = média entre repetições.


## Tabela 2 – Resumo dos relatos por ferramenta (união das repetições)

| Ferramenta | Relatos brutos | Após deduplicação | VP | FP | Inconclusivos |
|---|---|---|---|---|---|
| Schemathesis | 126 | 20 | 8 | 11 | 1 |
| RESTler | 5 | 4 | 4 | 0 | 0 |
| EvoMaster (caixa-preta) | 124 | 9 | 1 | 7 | 1 |

## Tabela 3 – Defeitos detectados e recall por ferramenta e API

| API | Defeitos no oráculo | Schemathesis VP (união) | Schemathesis Recall (união) | Schemathesis Recall (média) | RESTler VP (união) | RESTler Recall (união) | RESTler Recall (média) | EvoMaster (caixa-preta) VP (união) | EvoMaster (caixa-preta) Recall (união) | EvoMaster (caixa-preta) Recall (média) |
|---|---|---|---|---|---|---|---|---|---|---|
| vampi | 10 | 2 | 20.0% | 20.0% | 2 | 20.0% | 20.0% | 1 | 10.0% | 10.0% |
| Total | 10 | 2 | 20.0% | 20.0% | 2 | 20.0% | 20.0% | 1 | 10.0% | 10.0% |

## Sobreposição – defeitos por combinação de ferramentas

| API | Encontrado por | Defeitos |
|---|---|---|
| vampi | RESTler | 1 |
| vampi | Schemathesis + EvoMaster (caixa-preta) | 1 |
| vampi | Schemathesis + RESTler | 1 |
| vampi | Nenhuma ferramenta | 7 |

## Tabela 4 – Precisão e relatos inconclusivos por ferramenta

| Ferramenta | VP | FP | Precisão | Inconclusivos | Principal causa de FP |
|---|---|---|---|---|---|
| Schemathesis | 8 | 11 | 42.1% | 1 | [PRELIMINAR-IA] Especificação não documenta o Content-Type das respostas 401 (padrão do framework) |
| RESTler | 4 | 0 | 100.0% | 0 | — |
| EvoMaster (caixa-preta) | 1 | 7 | 12.5% | 1 | [PRELIMINAR-IA] Especificação não documenta o Content-Type das respostas 401 (padrão do framework) |

## Tabela 5 – Precisão, recall e F1-score (média das repetições)

| Ferramenta | Precisão (média) | Recall (média) | F1 (média) | F1 (mín–máx) |
|---|---|---|---|---|
| Schemathesis | 42.1% | 20.0% | 0.27 | 0.27–0.27 |
| RESTler | 100.0% | 20.0% | 0.33 | 0.33–0.33 |
| EvoMaster (caixa-preta) | 12.5% | 10.0% | 0.11 | 0.11–0.11 |

## Tabela 6 – Métricas de exploração e custo (média das repetições)

| Ferramenta | Cobertura de operações (%) | Nº de requisições | TTFF (min) | DPH |
|---|---|---|---|---|
| Schemathesis | 92.9 | 30379 | 0.1 | 12.00 |
| RESTler | 85.7 | 918 | 0.1 | 12.00 |
| EvoMaster (caixa-preta) | 92.9 | 46546 | 0.2 | 6.00 |

## Comparação par a par (Â12 > 0,5 favorece a primeira ferramenta)

| Métrica | Comparação | n | Â12 | p (Mann-Whitney) |
|---|---|---|---|---|
| recall | Schemathesis vs RESTler | 1/1 | 0.50 | — |
| recall | Schemathesis vs EvoMaster (caixa-preta) | 1/1 | 1.00 | — |
| recall | RESTler vs EvoMaster (caixa-preta) | 1/1 | 1.00 | — |
| precisao | Schemathesis vs RESTler | 1/1 | 0.00 | — |
| precisao | Schemathesis vs EvoMaster (caixa-preta) | 1/1 | 1.00 | — |
| precisao | RESTler vs EvoMaster (caixa-preta) | 1/1 | 1.00 | — |
| f1 | Schemathesis vs RESTler | 1/1 | 0.00 | — |
| f1 | Schemathesis vs EvoMaster (caixa-preta) | 1/1 | 1.00 | — |
| f1 | RESTler vs EvoMaster (caixa-preta) | 1/1 | 1.00 | — |
| cobertura_operacoes_pct | Schemathesis vs RESTler | 1/1 | 1.00 | — |
| cobertura_operacoes_pct | Schemathesis vs EvoMaster (caixa-preta) | 1/1 | 0.50 | — |
| cobertura_operacoes_pct | RESTler vs EvoMaster (caixa-preta) | 1/1 | 0.00 | — |
| dph | Schemathesis vs RESTler | 1/1 | 0.50 | — |
| dph | Schemathesis vs EvoMaster (caixa-preta) | 1/1 | 1.00 | — |
| dph | RESTler vs EvoMaster (caixa-preta) | 1/1 | 1.00 | — |