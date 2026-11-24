# Tabelas geradas automaticamente

Execuções consideradas: 27. Valores de média = média entre repetições.


## Tabela 2 – Resumo dos relatos por ferramenta (união das repetições)

| Ferramenta | Relatos brutos | Após deduplicação | VP | FP | Inconclusivos |
|---|---|---|---|---|---|
| Schemathesis | 83318 | 269 | 121 | 148 | 0 |
| RESTler | 122639 | 124 | 109 | 14 | 1 |
| EvoMaster (caixa-preta) | 310743 | 62 | 33 | 27 | 2 |

## Tabela 3 – Defeitos detectados e recall por ferramenta e API

| API | Defeitos no oráculo | Schemathesis VP (união) | Schemathesis Recall (união) | Schemathesis Recall (média) | RESTler VP (união) | RESTler Recall (união) | RESTler Recall (média) | EvoMaster (caixa-preta) VP (união) | EvoMaster (caixa-preta) Recall (união) | EvoMaster (caixa-preta) Recall (média) |
|---|---|---|---|---|---|---|---|---|---|---|
| catwatch | 8 | 8 | 100.0% | 95.8% | 7 | 87.5% | 87.5% | 7 | 87.5% | 87.5% |
| petclinic-rest | 13 | 11 | 84.6% | 76.9% | 7 | 53.8% | 53.8% | 7 | 53.8% | 53.8% |
| vampi | 12 | 4 | 33.3% | 33.3% | 2 | 16.7% | 16.7% | 2 | 16.7% | 16.7% |
| Total | 33 | 23 | 69.7% | 68.7% | 16 | 48.5% | 52.7% | 16 | 48.5% | 52.7% |

## Sobreposição – defeitos por combinação de ferramentas

| API | Encontrado por | Defeitos |
|---|---|---|
| catwatch | Schemathesis | 1 |
| catwatch | Schemathesis + RESTler + EvoMaster (caixa-preta) | 7 |
| catwatch | Nenhuma ferramenta | 0 |
| petclinic-rest | EvoMaster (caixa-preta) | 1 |
| petclinic-rest | RESTler | 1 |
| petclinic-rest | Schemathesis | 4 |
| petclinic-rest | Schemathesis + EvoMaster (caixa-preta) | 1 |
| petclinic-rest | Schemathesis + RESTler | 1 |
| petclinic-rest | Schemathesis + RESTler + EvoMaster (caixa-preta) | 5 |
| petclinic-rest | Nenhuma ferramenta | 0 |
| vampi | RESTler | 1 |
| vampi | Schemathesis | 1 |
| vampi | Schemathesis + EvoMaster (caixa-preta) | 2 |
| vampi | Schemathesis + RESTler | 1 |
| vampi | Nenhuma ferramenta | 7 |

## Tabela 4 – Precisão e relatos inconclusivos por ferramenta

| Ferramenta | VP | FP | Precisão | Inconclusivos | Principal causa de FP |
|---|---|---|---|---|---|
| Schemathesis | 121 | 148 | 45.0% | 0 | resposta sem corpo/sem Content-Type onde a especificação declara um tipo; sem falha da API (40 de 148) |
| RESTler | 109 | 14 | 88.6% | 1 | RESTler (InvalidDynamicObjectChecker, bucket 20x) anexou ?injected_query_string=123 ao caminho de um objeto válido e esperava erro; a API ignora o parâmetro desconhecido e devolve o objeto (20x), comportamento aceitável (8 de 14) |
| EvoMaster (caixa-preta) | 33 | 27 | 55.0% | 2 | endpoint interno /error do Spring Boot exposto pela especificação gerada automaticamente; chamado diretamente, sem erro anterior, responde 500 (status 999) por desenho do framework (13 de 27) |

## Tabela 5 – Precisão, recall e F1-score (média das repetições)

| Ferramenta | Precisão (média) | Recall (média) | F1 (média) | F1 (mín–máx) |
|---|---|---|---|---|
| Schemathesis | 42.5% | 68.7% | 0.47 | 0.40–0.60 |
| RESTler | 86.1% | 52.7% | 0.57 | 0.29–0.76 |
| EvoMaster (caixa-preta) | 54.7% | 52.7% | 0.48 | 0.19–0.70 |

## Tabela 6 – Métricas de exploração e custo (média das repetições)

| Ferramenta | Cobertura de operações (%) | Nº de requisições | TTFF (min) | DPH |
|---|---|---|---|---|
| Schemathesis | 72.7 | 97160 | 0.1 | 14.44 |
| RESTler | 67.2 | 57891 | 0.1 | 10.67 |
| EvoMaster (caixa-preta) | 70.6 | 225371 | 0.1 | 10.67 |

## Comparação par a par (Â12 > 0,5 favorece a primeira ferramenta)

| Métrica | Comparação | n | Â12 | p (Mann-Whitney) |
|---|---|---|---|---|
| recall | Schemathesis vs RESTler | 9/9 | 0.65 | 0.304 |
| recall | Schemathesis vs EvoMaster (caixa-preta) | 9/9 | 0.65 | 0.304 |
| recall | RESTler vs EvoMaster (caixa-preta) | 9/9 | 0.50 | 1.000 |
| precisao | Schemathesis vs RESTler | 9/9 | 0.00 | 0.000 |
| precisao | Schemathesis vs EvoMaster (caixa-preta) | 9/9 | 0.53 | 0.859 |
| precisao | RESTler vs EvoMaster (caixa-preta) | 9/9 | 0.72 | 0.114 |
| f1 | Schemathesis vs RESTler | 9/9 | 0.33 | 0.249 |
| f1 | Schemathesis vs EvoMaster (caixa-preta) | 9/9 | 0.43 | 0.658 |
| f1 | RESTler vs EvoMaster (caixa-preta) | 9/9 | 0.67 | 0.248 |
| cobertura_operacoes_pct | Schemathesis vs RESTler | 9/9 | 0.72 | 0.112 |
| cobertura_operacoes_pct | Schemathesis vs EvoMaster (caixa-preta) | 9/9 | 0.56 | 0.713 |
| cobertura_operacoes_pct | RESTler vs EvoMaster (caixa-preta) | 9/9 | 0.41 | 0.525 |
| dph | Schemathesis vs RESTler | 9/9 | 0.74 | 0.082 |
| dph | Schemathesis vs EvoMaster (caixa-preta) | 9/9 | 0.74 | 0.082 |
| dph | RESTler vs EvoMaster (caixa-preta) | 9/9 | 0.50 | 1.000 |

## Tabela 7 – Métricas por ferramenta e API: média (mínimo–máximo) entre as repetições

| API | Ferramenta | Repetições | Relatos brutos | Relatos únicos | VP | FP | INC | Defeitos detectados | Recall | Precisão | F1 | Cobertura de operações (%) | Requisições | TTFF (min) | DPH |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| catwatch | Schemathesis | 3 | 10180.3 (9962.0–10540.0) | 43.0 (41.0–45.0) | 12.3 (11.0–14.0) | 30.7 (30.0–31.0) | 0.0 (0.0–0.0) | 7.7 (7.0–8.0) | 95.8% (87.5%–100.0%) | 28.6% (26.8%–31.1%) | 0.44 (0.41–0.47) | 39.1 (39.1–39.1) | 66424 (65885–66854) | 0.1 (0.1–0.1) | 15.33 (14.00–16.00) |
| catwatch | RESTler | 3 | 4565.3 (4130.0–4904.0) | 19.0 (19.0–19.0) | 12.0 (12.0–12.0) | 6.0 (6.0–6.0) | 1.0 (1.0–1.0) | 7.0 (7.0–7.0) | 87.5% (87.5%–87.5%) | 66.7% (66.7%–66.7%) | 0.76 (0.76–0.76) | 39.1 (39.1–39.1) | 86566 (81969–92758) | 0.2 (0.1–0.2) | 14.00 (14.00–14.00) |
| catwatch | EvoMaster (caixa-preta) | 3 | 772.7 (750.0–791.0) | 35.0 (34.0–36.0) | 13.0 (12.0–14.0) | 20.0 (20.0–20.0) | 2.0 (2.0–2.0) | 7.0 (7.0–7.0) | 87.5% (87.5%–87.5%) | 39.4% (37.5%–41.2%) | 0.54 (0.53–0.56) | 39.1 (39.1–39.1) | 1626 (1593–1687) | 0.1 (0.0–0.1) | 14.00 (14.00–14.00) |
| petclinic-rest | Schemathesis | 3 | 17047.0 (16286.0–17977.0) | 176.7 (172.0–184.0) | 81.7 (78.0–86.0) | 95.0 (93.0–98.0) | 0.0 (0.0–0.0) | 10.0 (9.0–11.0) | 76.9% (69.2%–84.6%) | 46.2% (45.3%–46.7%) | 0.58 (0.56–0.60) | 86.0 (86.0–86.0) | 73677 (69024–81833) | 0.1 (0.1–0.2) | 20.00 (18.00–22.00) |
| petclinic-rest | RESTler | 3 | 36309.3 (33260.0–38835.0) | 95.3 (95.0–96.0) | 87.3 (87.0–88.0) | 8.0 (8.0–8.0) | 0.0 (0.0–0.0) | 7.0 (7.0–7.0) | 53.8% (53.8%–53.8%) | 91.6% (91.6%–91.7%) | 0.68 (0.68–0.68) | 76.7 (76.7–76.7) | 86196 (83319–89648) | 0.1 (0.1–0.2) | 14.00 (14.00–14.00) |
| petclinic-rest | EvoMaster (caixa-preta) | 3 | 102370.7 (98772.0–105507.0) | 16.0 (16.0–16.0) | 16.0 (16.0–16.0) | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) | 7.0 (7.0–7.0) | 53.8% (53.8%–53.8%) | 100.0% (100.0%–100.0%) | 0.70 (0.70–0.70) | 79.8 (76.7–83.7) | 491784 (488797–493538) | 0.1 (0.1–0.1) | 14.00 (14.00–14.00) |
| vampi | Schemathesis | 3 | 545.3 (529.0–563.0) | 23.3 (22.0–26.0) | 12.3 (11.0–15.0) | 11.0 (11.0–11.0) | 0.0 (0.0–0.0) | 4.0 (4.0–4.0) | 33.3% (33.3%–33.3%) | 52.6% (50.0%–57.7%) | 0.41 (0.40–0.42) | 92.9 (92.9–92.9) | 151379 (144351–162333) | 0.1 (0.1–0.1) | 8.00 (8.00–8.00) |
| vampi | RESTler | 3 | 5.0 (5.0–5.0) | 4.0 (4.0–4.0) | 4.0 (4.0–4.0) | 0.0 (0.0–0.0) | 0.0 (0.0–0.0) | 2.0 (2.0–2.0) | 16.7% (16.7%–16.7%) | 100.0% (100.0%–100.0%) | 0.29 (0.29–0.29) | 85.7 (85.7–85.7) | 910 (902–918) | 0.2 (0.1–0.2) | 4.00 (4.00–4.00) |
| vampi | EvoMaster (caixa-preta) | 3 | 437.7 (421.0–454.0) | 9.3 (9.0–10.0) | 2.3 (2.0–3.0) | 7.0 (7.0–7.0) | 0.0 (0.0–0.0) | 2.0 (2.0–2.0) | 16.7% (16.7%–16.7%) | 24.8% (22.2%–30.0%) | 0.20 (0.19–0.21) | 92.9 (92.9–92.9) | 182704 (178587–190026) | 0.1 (0.1–0.1) | 4.00 (4.00–4.00) |

## Comparação par a par por API (com n = 3 por grupo, o menor p bilateral possível do Mann-Whitney é 0,10)

| API | Métrica | Comparação | n | Â12 | p (Mann-Whitney) |
|---|---|---|---|---|---|
| catwatch | recall | Schemathesis vs RESTler | 3/3 | 0.83 | 0.188 |
| catwatch | recall | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 0.83 | 0.188 |
| catwatch | recall | RESTler vs EvoMaster (caixa-preta) | 3/3 | 0.50 | — |
| catwatch | precisao | Schemathesis vs RESTler | 3/3 | 0.00 | 0.064 |
| catwatch | precisao | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 0.00 | 0.100 |
| catwatch | precisao | RESTler vs EvoMaster (caixa-preta) | 3/3 | 1.00 | 0.064 |
| catwatch | f1 | Schemathesis vs RESTler | 3/3 | 0.00 | 0.064 |
| catwatch | f1 | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 0.00 | 0.100 |
| catwatch | f1 | RESTler vs EvoMaster (caixa-preta) | 3/3 | 1.00 | 0.064 |
| catwatch | cobertura_operacoes_pct | Schemathesis vs RESTler | 3/3 | 0.50 | — |
| catwatch | cobertura_operacoes_pct | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 0.50 | — |
| catwatch | cobertura_operacoes_pct | RESTler vs EvoMaster (caixa-preta) | 3/3 | 0.50 | — |
| catwatch | requisicoes | Schemathesis vs RESTler | 3/3 | 0.00 | 0.100 |
| catwatch | requisicoes | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 1.00 | 0.100 |
| catwatch | requisicoes | RESTler vs EvoMaster (caixa-preta) | 3/3 | 1.00 | 0.100 |
| catwatch | dph | Schemathesis vs RESTler | 3/3 | 0.83 | 0.188 |
| catwatch | dph | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 0.83 | 0.188 |
| catwatch | dph | RESTler vs EvoMaster (caixa-preta) | 3/3 | 0.50 | — |
| petclinic-rest | recall | Schemathesis vs RESTler | 3/3 | 1.00 | 0.064 |
| petclinic-rest | recall | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 1.00 | 0.064 |
| petclinic-rest | recall | RESTler vs EvoMaster (caixa-preta) | 3/3 | 0.50 | — |
| petclinic-rest | precisao | Schemathesis vs RESTler | 3/3 | 0.00 | 0.077 |
| petclinic-rest | precisao | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 0.00 | 0.064 |
| petclinic-rest | precisao | RESTler vs EvoMaster (caixa-preta) | 3/3 | 0.00 | 0.059 |
| petclinic-rest | f1 | Schemathesis vs RESTler | 3/3 | 0.00 | 0.077 |
| petclinic-rest | f1 | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 0.00 | 0.064 |
| petclinic-rest | f1 | RESTler vs EvoMaster (caixa-preta) | 3/3 | 0.00 | 0.059 |
| petclinic-rest | cobertura_operacoes_pct | Schemathesis vs RESTler | 3/3 | 1.00 | 0.047 |
| petclinic-rest | cobertura_operacoes_pct | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 1.00 | 0.064 |
| petclinic-rest | cobertura_operacoes_pct | RESTler vs EvoMaster (caixa-preta) | 3/3 | 0.17 | 0.197 |
| petclinic-rest | requisicoes | Schemathesis vs RESTler | 3/3 | 0.00 | 0.100 |
| petclinic-rest | requisicoes | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 0.00 | 0.100 |
| petclinic-rest | requisicoes | RESTler vs EvoMaster (caixa-preta) | 3/3 | 0.00 | 0.100 |
| petclinic-rest | dph | Schemathesis vs RESTler | 3/3 | 1.00 | 0.064 |
| petclinic-rest | dph | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 1.00 | 0.064 |
| petclinic-rest | dph | RESTler vs EvoMaster (caixa-preta) | 3/3 | 0.50 | — |
| vampi | recall | Schemathesis vs RESTler | 3/3 | 1.00 | 0.047 |
| vampi | recall | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 1.00 | 0.047 |
| vampi | recall | RESTler vs EvoMaster (caixa-preta) | 3/3 | 0.50 | — |
| vampi | precisao | Schemathesis vs RESTler | 3/3 | 0.00 | 0.059 |
| vampi | precisao | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 1.00 | 0.072 |
| vampi | precisao | RESTler vs EvoMaster (caixa-preta) | 3/3 | 1.00 | 0.059 |
| vampi | f1 | Schemathesis vs RESTler | 3/3 | 1.00 | 0.059 |
| vampi | f1 | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 1.00 | 0.072 |
| vampi | f1 | RESTler vs EvoMaster (caixa-preta) | 3/3 | 1.00 | 0.059 |
| vampi | cobertura_operacoes_pct | Schemathesis vs RESTler | 3/3 | 1.00 | 0.047 |
| vampi | cobertura_operacoes_pct | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 0.50 | — |
| vampi | cobertura_operacoes_pct | RESTler vs EvoMaster (caixa-preta) | 3/3 | 0.00 | 0.047 |
| vampi | requisicoes | Schemathesis vs RESTler | 3/3 | 1.00 | 0.100 |
| vampi | requisicoes | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 0.00 | 0.100 |
| vampi | requisicoes | RESTler vs EvoMaster (caixa-preta) | 3/3 | 0.00 | 0.100 |
| vampi | dph | Schemathesis vs RESTler | 3/3 | 1.00 | 0.047 |
| vampi | dph | Schemathesis vs EvoMaster (caixa-preta) | 3/3 | 1.00 | 0.047 |
| vampi | dph | RESTler vs EvoMaster (caixa-preta) | 3/3 | 0.50 | — |