# Relatório de passagem: preparação do experimento (2026-11-23)

Este arquivo resume o estado da preparação para continuar o trabalho em outra
máquina. Ele acompanha o repositório (`fuzz-apis-rest/`). Detalhes de cada mudança
estão em `docs/desvios.md`; versões e imagens em `docs/versoes.md`.

## 1. Regras do estudo (inegociáveis)

- Nunca inventar, editar ou "corrigir" dados coletados em `data/raw/`.
- Não preencher a coluna `classificacao` (VP/FP/INC); isso é feito manualmente pela
  equipe. Uma coluna separada `sugestao_ia` só se a equipe pedir.
- Toda mudança de método (orçamento, versões, parâmetros, APIs) vai para
  `docs/desvios.md`, com data e motivo.
- As requisições de reprodução das vulnerabilidades do VAmPI (coluna
  `como_reproduzir` do `oraculo.csv`) **ficam com a equipe**. O assistente não as
  escreveu, e todas as linhas continuam com `verificado=nao`.

## 2. Situação das etapas do plano original

| Etapa | Situação |
|---|---|
| 1. Pré-requisitos | Feita na máquina anterior. **Refazer na nova** (seção 3). |
| 2. Especificação, imagens e versões fixadas | Feita. Todas as imagens estão fixadas por digest. `docs/versoes.md` tem a seção "Máquina" da máquina **anterior**: **atualizar com a máquina que rodar as campanhas** (Tabela 1). |
| 3. Credenciais e oráculo do VAmPI | Credenciais conferidas no código (`name1`/`pass1`, `get_token.sh` ok). Corrigido o nome da operação VAMPI-03 (`{book_title}`). `como_reproduzir`/`verificado` ficam com a equipe. |
| 4. Teste rápido | **Em andamento.** Vários problemas foram encontrados e corrigidos (seção 4). Falta uma rodada completa do teste com todas as correções (seção 5). |
| 5. APIs do WFD | Escolhidas **petclinic-rest** e **catwatch** (decisão delegada ao assistente; critérios e descartes em D09). Já adicionadas (`apis/petclinic-rest/`, `apis/catwatch/`). O oráculo delas começa vazio e será formado por *pooling* (D10). |
| 6. Campanhas completas | Não iniciadas. Estimativa: 27 execuções × (30 min + ~2 min de preparação) ≈ **14,5 h**. |
| 7. Extração e contagem de relatos | Não iniciada (depende da 6). |
| 8. Git e GitHub | Não iniciados. Ainda não há repositório git. Publicar só com confirmação. |

## 3. Preparar a nova máquina

Requisitos: Linux nativo ou WSL2 com Ubuntu. Use o Docker Engine nativo (no WSL, não
o Docker Desktop), porque os wrappers usam `--network host`.

```bash
sudo apt update && sudo apt install -y python3 python3-yaml python3-scipy curl git tmux docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker $USER      # reabrir o terminal depois
# copiar o repositório para o sistema de arquivos do Linux (no WSL, não em /mnt/c)
cd ~ && unzip /caminho/fuzz-apis-rest-passagem.zip
cd fuzz-apis-rest && chmod 755 scripts/*.sh tools/*.sh apis/*/*.sh analysis/*.py
# baixar as imagens fixadas: lista no README, seção "1. Preparar"
```

No WSL: dê ao WSL pelo menos 8 a 12 GB de RAM (`%UserProfile%\.wslconfig`:
`[wsl2]` / `memory=12GB`). Mantenha a distribuição viva durante as campanhas:
- deixe um terminal aberto; ou
- rode, no PowerShell, `Start-Process wsl.exe -ArgumentList '-d','Ubuntu-24.04','--','sleep','infinity' -WindowStyle Hidden`.

Desative a suspensão do computador (`powercfg /change standby-timeout-ac 0`).

**Atenção:** editar arquivos pelo caminho `\\wsl.localhost\...` no Windows remove o
bit de execução. Rode o `chmod` acima antes de cada execução.

## 4. Problemas encontrados e corrigidos (detalhes em `docs/desvios.md`)

| ID | Problema | Correção |
|---|---|---|
| D03 | Execução interrompida era pulada para sempre ao retomar | Só conta como concluída com `meta.json`; as incompletas são movidas para `data/raw/_incompletas/` |
| D04 | `/createdb` do VAmPI às vezes falha (colisão aleatória de títulos de livro) e derrubava o script | Até 5 tentativas; falhas isoladas não derrubam a campanha |
| D05 | Schemathesis: a última iteração era morta sem gravar o relatório | Usa `--max-time` nativo da 4.34 |
| D07 | `BUDGET_MIN=2 REPS=1` era sobrescrito pelo `experiment.env` (o teste rodava com 30 min) | A linha de comando tem precedência |
| D08 | catwatch `GET /fetch` acessa a API do GitHub | APIs em rede Docker interna, sem internet (as três) |
| D11 | RESTler v8.5.0 quebrava no modo fuzz (`ValueError` em `headers_dict`) | **RESTler v9.2.4** para todas as APIs |
| D12 | Schemathesis sem permissão para gravar o relatório (abortava em 13 s) | `--user uid:gid` |
| D13 | RESTler gerava `//config` na catwatch (`basePath: "/"`) | Opção `basepath: ""` do motor, sem editar a especificação |
| D14 | EvoMaster chamava `/petclinic/petclinic/...` (100% de respostas 500) | `--bbTargetUrl` só com a origem |

Parsers ajustados aos formatos reais (`analysis/extract_findings.py`), sem efeito sobre dados:
- **Schemathesis 4.34 (JUnit):** lê as linhas `- STxxx <checagem>` de cada falha; ST101 (5xx) fica com o proxy; o exemplo é o `curl` de reprodução do próprio relatório.
- **EvoMaster 5.1:** lê `generated_tests/report.json` (formato WFC: `faults.foundFaults[].operationId` + `faultCategories[].code/context`); código 100 (HTTP 500) fica com o proxy.
- **RESTler:** o formato dos *bug buckets* (`<checker>_<status>_<n>.txt`, linhas `-> GET /...`) bate com o parser original.
- **Assinatura de 5xx (proxy):** usa o `<title>` de páginas HTML de erro (Werkzeug) e descarta campos voláteis de corpos JSON (`timestamp`, `instance`, `path`, `type`). Sem isso, cada ID virava um relato diferente: o primeiro teste deu 4.594 "relatos únicos", quase todos repetidos.

## 5. O que o último teste rápido mostrou e o que falta conferir

Com as correções, foram rodados só os três do VAmPI (os outros foram interrompidos):
- `vampi__evomaster__rep1`: 13.015 requisições; 8 falhas no `report.json` (código 101, conformidade de esquema).
- `vampi__restler__rep1` (v9.2.4): 918 requisições; um *bucket* `InvalidValueChecker 500` em `GET /users/v1/{username}`. Conferir se o RESTler morto ao fim do orçamento ainda grava os *bug buckets* (gravados durante a execução).
- `vampi__schemathesis__rep1`: 10.484 requisições; JUnit com 15 casos e 11 falhas (ST101, ST103, ST105, ST108, ST202, ST302). Foi interrompido antes de gravar `meta.json`.

**Falta rodar o teste rápido completo, com as três APIs, e conferir:**
1. petclinic-rest: o RESTler v9.2.4 não aborta no fuzz; a EvoMaster chama `/petclinic/api/...` (não `/petclinic/petclinic`).
2. catwatch: o RESTler chama `/config` (não `//config`); as três ferramentas têm um número razoável de requisições.
3. Schemathesis nas três APIs: `iter_0/junit-*.xml` existe e não há `Permission denied`.
4. `data/processed/achados_por_execucao.csv` tem achados próprios de cada ferramenta (`schemathesis:ST…`, `restler:<Checker>`, `evomaster:<código>`), e o número de relatos únicos é razoável (dezenas, não milhares).
5. Depois, apagar os dados de teste: `rm -rf data/raw/*__* data/raw/_incompletas data/processed data/validated/relatos.csv`.

## 6. Próximos passos

1. Preparar a máquina (seção 3) e atualizar a seção "Máquina" de `docs/versoes.md`.
2. Teste rápido: `BUDGET_MIN=2 REPS=1 APIS="vampi petclinic-rest catwatch" ./scripts/run_campaigns.sh && python3 analysis/extract_findings.py`. Validar os itens da seção 5.
3. Campanhas: `./scripts/start_background.sh` (tmux, log em `campaigns.log`); progresso com `./scripts/progress.sh` ou `tmux attach -t campanhas`. Para retomar, rode o mesmo comando de novo.
4. Ao final, `python3 analysis/extract_findings.py` e contagem de relatos únicos por API e ferramenta para a validação manual.
5. `git init`, commits organizados e publicação no GitHub (público, citado no artigo), só com confirmação da equipe.
