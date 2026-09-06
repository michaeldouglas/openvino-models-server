# Feature Specification: OpenVINO Model Server API

**Feature Branch**: `feature/implement-openvino-models-server`

**Spec Kit Feature**: `001-fastapi-openvino-inference`

**Created**: 2026-09-06

**Status**: Ready for implementation

**Input**: Implementar a primeira versão do `openvino-models-server` com FastAPI,
Docker Compose, OpenVINO Model Server (OVMS) na GPU Intel e geração síncrona,
assíncrona e em streaming.

## User Scenarios & Testing

### User Story 1 - Gerar uma resposta completa (Priority: P1)

Como consumidor, quero enviar um texto ao serviço e receber uma resposta completa
de um LLM local servido por OVMS.

**Why this priority**: É o valor central da primeira versão.

**Independent Test**: Com o upstream substituído por um servidor controlado,
enviar um texto válido às rotas sync e async e verificar resposta, modelo e
motivo de término.

**Acceptance Scenarios**:

1. **Given** um OVMS pronto, **When** o cliente envia texto válido a
   `POST /v1/generate/sync`, **Then** recebe JSON com `request_id`, `model`,
   `text` e `finish_reason`.
2. **Given** um OVMS pronto, **When** o cliente envia texto válido a
   `POST /v1/generate/async`, **Then** recebe o mesmo contrato sem bloquear o
   event loop durante a chamada HTTP ao upstream.
3. **Given** texto ausente, vazio ou acima do limite, **When** qualquer rota é
   chamada, **Then** retorna erro de validação sem chamar o OVMS.

### User Story 2 - Receber geração incremental (Priority: P1)

Como consumidor, quero receber deltas reais enquanto o OVMS gera a resposta,
para exibir o resultado sem aguardar o fim da geração.

**Independent Test**: Com um upstream controlado que envia dois eventos antes
do término, confirmar que `POST /v1/generate/stream` transmite os dois deltas,
um evento `done` e permite reconstruir o texto por concatenação.

**Acceptance Scenarios**:

1. **Given** um upstream que suporta streaming, **When** o cliente chama a rota
   stream, **Then** recebe `Content-Type: text/event-stream` e eventos `delta`,
   `done` ou `error` em JSON.
2. **Given** uma falha depois do envio dos headers, **When** a falha ocorre,
   **Then** o serviço envia evento `error` e fecha o upstream sem tentar trocar
   o status HTTP da resposta já iniciada.
3. **Given** o cliente desconecta ou o timeout vence, **When** o stream é
   encerrado, **Then** o upstream e os recursos da conexão são fechados.

### User Story 3 - Operar a stack de forma reproduzível (Priority: P1)

Como operador, quero iniciar API e OVMS por Docker Compose, verificar saúde e
prontidão sem executar geração em health checks, e consultar o Swagger.

**Independent Test**: Com artefato de modelo persistido e ambiente GPU preparado,
executar `docker compose up -d --build`, consultar liveness/readiness, abrir
`/docs` e realizar uma geração real.

**Acceptance Scenarios**:

1. **Given** Docker Desktop/Linux com acesso GPU Intel comprovado, **When** a
   stack inicia, **Then** a API fica publicada somente em localhost e o OVMS
   fica acessível apenas na rede interna.
2. **Given** o modelo ainda não está pronto, **When** `/readyz` é consultado,
   **Then** retorna estado não pronto com causa segura e acionável.
3. **Given** os serviços estão ativos, **When** `/healthz`, `/docs` e
   `/openapi.json` são consultados, **Then** os três contratos respondem sem
   iniciar uma geração.

### Edge Cases

- Corpo ausente, JSON inválido, tipo incorreto, texto vazio ou somente espaços.
- `max_tokens` e `temperature` ausentes, no limite e fora dos limites.
- Timeout, indisponibilidade, resposta inválida, desconexão e erro HTTP do OVMS.
- Fragmentos SSE sem conteúdo, eventos maiores que o limite ou `[DONE]` sem
  texto final.
- Duas requisições simultâneas não podem compartilhar histórico, texto ou
  resposta; a concorrência deve ser limitada explicitamente.
- O modelo não pode ser escolhido pelo cliente por URL, caminho local ou nome
  arbitrário.
- Logs não devem registrar prompts, respostas completas, segredos ou caminhos
  pessoais por padrão.

## Requirements

### Functional Requirements

- **FR-001**: O sistema MUST expor exatamente `POST /v1/generate/sync`,
  `POST /v1/generate/async` e `POST /v1/generate/stream`, além de liveness,
  readiness e documentação OpenAPI.
- **FR-002**: As três rotas MUST aceitar `text` obrigatório e parâmetros
  opcionais `max_tokens` e `temperature`, com defaults e limites configurados.
- **FR-003**: Sync MUST executar I/O bloqueante fora do event loop; async MUST
  usar I/O HTTP não bloqueante com `async/await`; ambas aguardam o resultado na
  mesma requisição e não são fila de jobs.
- **FR-004**: A rota stream MUST encaminhar deltas disponibilizados pelo OVMS em
  SSE real com eventos `delta`, `done` e `error`; a concatenação dos deltas deve
  reconstruir o texto.
- **FR-005**: As respostas JSON MUST conter `request_id`, `model`, `text` e
  `finish_reason`; uso de tokens só pode aparecer quando fornecido ou medido.
- **FR-006**: A API MUST chamar OVMS pela rede interna do Compose, mantendo o
  modelo carregado somente no serviço `ovms`, sem cópia ou carregamento por
  requisição no FastAPI.
- **FR-007**: O OVMS MUST usar imagem versionada, modelo identificado por nome e
  revisão, armazenamento persistente e dispositivo `GPU` explícito, sem
  fallback silencioso para CPU.
- **FR-008**: A configuração MUST vir de ambiente documentado, com limites de
  entrada, contexto, geração, concorrência e timeout validados no startup.
- **FR-009**: `/healthz` MUST verificar apenas liveness da API e `/readyz` MUST
  verificar capacidade do OVMS/modelo correto sem gerar texto.
- **FR-010**: Falhas de entrada, capacidade, upstream indisponível, upstream,
  timeout e stream MUST usar códigos e mensagens seguros e consistentes, sem
  stack trace para o cliente.
- **FR-011**: Requisições MUST ser independentes e não manter histórico
  compartilhado nem aceitar seleção de modelo pelo cliente.
- **FR-012**: A solução MUST incluir Dockerfile, Compose, `.env.example`,
  configuração do OVMS, documentação em português, Swagger e exemplos curl
  para PowerShell/Windows e Linux.
- **FR-013**: A solução MUST incluir testes unitários e de integração HTTP com
  upstream controlado para validação, sync/async, parsing SSE, timeout, erro e
  desconexão, executáveis sem GPU e sem download de LLM.
- **FR-014**: A preparação futura do modelo MUST ser idempotente, preservar
  originais e manter artefatos persistentes em `app/models/`, fora do Git.
- **FR-015**: A implementação MUST registrar versão da imagem OVMS, nome/revisão
  do modelo, precisão, dispositivo e evidências de cada validação, distinguindo
  configuração de execução real.
- **FR-016**: A solução MUST medir, quando a validação real for possível, tempo
  de inicialização/compilação, primeira chamada, chamadas aquecidas, TTFT,
  latência total, tokens por segundo e concorrência pequena, sem prometer
  desempenho não medido.

## Key Entities

- **GenerationRequest**: texto e parâmetros de geração validados.
- **GenerationResult**: request ID, modelo, texto, término e uso opcional.
- **StreamEvent**: evento SSE `delta`, `done` ou `error` em JSON.
- **InferenceProvider**: contrato interno para geração completa, stream e
  readiness, independente de FastAPI e dos detalhes HTTP de OVMS.
- **RuntimeConfiguration**: endpoint interno, modelo, limites, timeouts,
  concorrência e dispositivo esperado.
- **OperationalEvidence**: registro de versão, modelo, precisão, dispositivo,
  comando, resultado e limitação da validação.

## Success Criteria

### Measurable Outcomes

- **SC-001**: As três rotas passam 100% dos testes de contrato, validação e
  falhas controladas sem GPU nem modelo baixado.
- **SC-002**: 100% das entradas inválidas são rejeitadas antes da chamada ao
  upstream e retornam erro que identifica a correção necessária.
- **SC-003**: Em ambiente real validado, as três rotas respondem com o modelo
  selecionado e o streaming entrega pelo menos um delta antes do evento done.
- **SC-004**: A stack documentada expõe `/docs`, `/openapi.json`, liveness e
  readiness; a API é publicada somente em `127.0.0.1` por padrão.
- **SC-005**: Nenhum segredo, prompt completo, resposta completa ou modelo é
  versionado por engano; testes, lint e tipagem passam com evidências.
- **SC-006**: O relatório de desempenho separa inicialização, primeira chamada,
  aquecimento e concorrência, identificando modelo, revisão, precisão,
  dispositivo e condições de execução.

## Assumptions and Decisions

- A arquitetura desta versão é `api` (FastAPI) + `ovms` (OpenVINO Model
  Server), comunicando-se por rede interna Docker Compose.
- Candidato recomendado para a primeira validação: `OpenVINO/Qwen3-1.7B-int4-ov`,
  revisão `main` registrada no preparo; candidatos alternativos são
  `OpenVINO/Qwen2.5-1.5B-Instruct-int4-ov` e `OpenVINO/Qwen3-4B-int4-ov`.
  A recomendação é de planejamento, não evidência de qualidade ou GPU.
- A imagem inicial planejada é `openvino/model_server:2026.3.1-gpu`, fixada
  também por digest quando o manifesto puder ser verificado no ambiente. O
  tag foi escolhido por ser uma release GPU versionada; a execução ainda exige
  validação de acesso Intel GPU no Docker Desktop/WSL2.
- No Windows, o procedimento de GPU deve usar somente a configuração WSL2
  documentada (`/dev/dxg` e mount `/usr/lib/wsl`) depois de confirmar que WSL2 e
  o daemon efetivamente utilizado expõem esses recursos. Não se presume que a
  GPU visível no host esteja disponível no container.
- OVMS é o serviço de inferência escolhido; OVMS será preferido a um runtime
  dentro da API e só será substituído se evidência futura justificar outra
  arquitetura.
- Autenticação, exposição pública, conversas persistentes, filas, banco,
  Redis, Celery, LangChain e frontend estão fora desta versão.
