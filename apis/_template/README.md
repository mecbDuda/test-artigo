# Como adicionar uma nova API alvo

1. Copie esta pasta para `apis/<nome-da-api>/`.
2. Crie `docker-compose.yml` com dois serviços, como em `apis/vampi/`:
   - `api`: a API alvo **sem** porta publicada;
   - `proxy`: o mitmproxy em modo reverso, apontando para a porta interna da API
     e publicando a porta `8080`. Copie o bloco `proxy` do VAmPI e troque só
     `reverse:http://api:<porta>`.
   - Para APIs do Web Fuzzing Dataset (WFD), use as imagens/arquivos de
     `https://github.com/WebFuzzing/Dataset` (pasta `dockerfiles`) para o serviço
     `api` e mantenha o nosso `proxy` na frente.
3. Crie `api.env` com `API_NAME`, `SCHEMA_FILE`, `BASE_URL`, `HEALTH_URL`,
   `INIT_CMD` (comando que restaura o estado inicial; use `true` se recriar o
   contêiner já basta) e, se houver autenticação, `AUTH_SCRIPT`.
4. Salve a especificação OpenAPI no caminho de `SCHEMA_FILE` e valide-a
   (por exemplo, em https://editor.swagger.io).
5. Registre os defeitos conhecidos da API em `data/ground_truth/oraculo.csv`.
6. Faça um teste curto: `BUDGET_MIN=2 REPS=1 APIS=<nome> ./scripts/run_campaigns.sh`.
