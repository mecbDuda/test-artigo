# Versões e ambiente de execução

Registro do que foi efetivamente usado no experimento (Tabela 1 e Quadro 3 do artigo).
Levantado em 2026-11-22. As imagens são fixadas por **digest** em
`config/experiment.env` e `apis/<api>/docker-compose.yml`. Com o digest, o
Docker sempre baixa exatamente a mesma imagem, mesmo que a tag mude depois.

## Ferramentas (Quadro 3)

| Ferramenta | Versão | Imagem Docker | Digest | Imagem criada em |
|---|---|---|---|---|
| Schemathesis | 4.34.0 | `schemathesis/schemathesis:4.34.0` | `sha256:7aa27b2085e944c81f5225c52c29bf072778bb5d59e6b27e1876b4757e266a14` | 2026-11-22 |
| RESTler | 9.2.4 | `mcr.microsoft.com/restlerfuzzer/restler:v9.2.4` | `sha256:f37705fc4a11071f1de67ac4708fd97c71c1b4e5a0bc0f9c16c21028c0c41cbb` | 2024-03-06 |
| EvoMaster (caixa-preta) | 5.1.0 | `webfuzzing/evomaster:v5.1.0` | `sha256:cf02675504a0b51c268c9320e7d6f7fce92e038c62d5a0bdb25e175ea86c0c89` | 2026-03-17 |

Observações:
- A tag `schemathesis:stable` apontava, em 2026-11-22, para a 4.34.0 (mesmo digest).
- O RESTler planejado era o v8.5.0 (`sha256:5e22d3ca…`, de 2022-03-23). Ele foi trocado pelo v9.2.4 por causa de uma falha do motor no modo fuzz (ver `docs/desvios.md`, D11).
- O EvoMaster roda com `-Xmx4G`, que é o padrão da imagem.

## Infraestrutura de medição

| Componente | Versão | Imagem | Digest |
|---|---|---|---|
| mitmproxy (proxy de captura) | 10.3.0 (Python 3.11.9) | `mitmproxy/mitmproxy:10.3.0` | `sha256:a22a4f2178ac5876598402c7060868ec96e90710b31e768ed25a57f501d9f48d` |

## APIs alvo (Tabela 1)

| API | Versão | Imagem | Digest | Especificação |
|---|---|---|---|---|
| VAmPI | `latest` de 2026-04-07 (Flask 2.2.2, connexion 2.14.2, Python 3.11.15) | `erev0s/vampi:latest` | `sha256:0a5a224b6e14ae7da6a6ea265178ff71286ff903aec74adee98f660bb0e4ca12` | `apis/vampi/openapi3.yml`: OpenAPI 3, 14 operações, sha256 `35200f354f9c9968182fc19458295ed45bb4c368150348c46d5146a7e40a61c9`, idêntica à embutida na imagem |

| petclinic-rest (WFD) | tag `FINAL` de 2026-11-13 (Java 17, Spring Boot, H2 em memória) | `webfuzzing/wfd-petclinic-rest:FINAL` | `sha256:ea7d5dcc6d0144479c8636ab0b0cc1125f29e30b5e9f0c08e64e6e820ed1a70f` | `apis/petclinic-rest/openapi.json`: OpenAPI 3.1.0, 43 operações, sha256 `5349df50f785058c41e2889ed7eed379bb028796820378c49ad4776f1f58f06c`, de `openapi/petclinic-rest.json` do WFD |
| catwatch (WFD) | tag `FINAL` de 2026-11-13 (Java 8, Spring Boot, H2 em memória) | `webfuzzing/wfd-catwatch:FINAL` | `sha256:814cfa76226f4e0f2adb01aa4eba95bc296971a25ac20a33be597b1fd1d68ef2` | `apis/catwatch/openapi.json`: Swagger 2.0, 23 operações, sha256 `a57c28730993b6f2bdc8f0436e54344ed2a45b22eb06136a492d62142d0b20cb`, de `openapi/catwatch.json` do WFD |

Configuração do VAmPI: `vulnerable=1`, `tokentimetolive=7200`. As três APIs rodam numa rede Docker interna, sem acesso à internet; só o proxy é exposto.
Autenticação: VAmPI usa JWT Bearer (login de `name1`); petclinic-rest e catwatch não têm autenticação.

## Máquina

### Campanha completa

A campanha completa (27 execuções, a partir de 2026-11-23 à noite) rodou nesta
máquina, a mesma da preparação, com **2 slots paralelos** (`docs/desvios.md`, D21 a D26).

| Item | Valor |
|---|---|
| Ambiente | PC desktop com Windows 11 Pro (10.0.26300) e WSL 2.4.13 (Ubuntu 24.04.5 LTS, kernel 5.15.167.4-microsoft-standard-WSL2); Docker Engine nativo no WSL, não o Docker Desktop |
| CPU | Intel Core i5-13400F, 10 núcleos (6P + 4E), 16 threads (`nproc` = 16) |
| RAM | 16 GB físicos (15,8 GiB visíveis no Windows); 12 GB alocados ao WSL (`.wslconfig`), 11.964 MiB visíveis no Linux; swap de 3 GiB |
| Disco | disco virtual ext4 do WSL (1.007 GB, 950 GB livres) |
| Docker | Docker Engine 29.1.3, storage overlayfs, cgroup v1 (cgroupfs) |
| Docker Compose | 2.40.3 |
| Python | 3.12.3 (pyyaml 6.0.1, scipy 1.11.4) |
| curl / tmux / git | 8.5.0 / 3.4 / 2.43.0 |
| Rede | `--network host` testado e funcionando (`docker run --rm --network host alpine wget …`) |

Limites por contêiner em cada slot (`scripts/limites.sh 2`; iguais para as três ferramentas):

| Contêiner | CPUs | Memória |
|---|---|---|
| Ferramenta (Schemathesis, RESTler ou EvoMaster) | 4,00 | 3.038 MiB |
| API alvo | 2,00 | 1.536 MiB (APIs Java com `-Xmx1152m`) |
| Proxy (mitmproxy) | 1,00 | 384 MiB |
| Reserva para o sistema | 2 CPUs | 2.048 MiB |

### Codespace (estudo piloto e campanha interrompida)

O estudo piloto (branch `piloto`, pasta `piloto/`) e uma primeira tentativa de
campanha, sequencial e interrompida após 6 execuções (D21; dados em
`campanha_codespace/`), rodaram num GitHub Codespace:

| Item | Valor |
|---|---|
| Ambiente | GitHub Codespace, tipo "2 cores, 8 GB RAM, 32 GB storage" (VM Azure), tempo de ociosidade de 240 min |
| CPU | AMD EPYC 7763, 2 vCPUs (`nproc` = 2) |
| RAM | 7,8 GiB (`free -h`), sem swap |
| Disco | 32 GB (overlay); `/tmp` em disco separado de 44 GB |
| SO | Ubuntu 24.04.5 LTS, kernel 6.8.0-1070-azure |
| Docker | Docker Engine 29.9.2, storage overlayfs |
| Docker Compose | v5.6.1 |
| Python | 3.14.2 (pyyaml 6.0.3, scipy 1.18.1) |
| curl | 8.5.0 |
| tmux | 3.4 |
