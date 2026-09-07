# Feature Specification: Observabilidade de desempenho com GuideLLM

**Feature Branch**: `feature/guidellm-observability`
**Created**: 2026-09-06
**Status**: Implemented and validated locally
**Input**: User description: integrar GuideLLM ao Compose para medir desempenho real do OVMS e tokens por segundo.

## User Scenarios & Testing

### User Story 1 - Executar benchmark direto no OVMS (Priority: P1)

Como operador, quero executar um benchmark curto contra o endpoint OpenAI-compatible do OVMS para medir o comportamento real do modelo sem alterar o contrato do FastAPI.

**Independent Test**: Com `api` e `ovms` saudáveis, executar o comando do harness com concorrência 1 e verificar relatórios não vazios.

### User Story 2 - Consultar métricas de geração (Priority: P1)

Como operador, quero encontrar tokens de entrada/saída, tokens por segundo, TTFT, latência, percentis, requisições concluídas e falhas em formatos reutilizáveis.

**Independent Test**: Abrir `benchmarks.json`, `benchmarks.csv` e `benchmarks.html` de uma execução real e conferir o modelo, configuração e métricas registrados.

### User Story 3 - Repetir e ajustar a medição (Priority: P2)

Como operador, quero escolher modelo, entrada, saída, concorrência, quantidade de requisições e duração sem duplicar pesos ou instalar dependências de produção.

**Independent Test**: Reexecutar o script com outro alias ou limite e verificar que cada execução recebe uma pasta distinta em `.agent-work`.

## Requirements

- **FR-001**: O Compose MUST declarar um serviço `guidellm` separado, com imagem versionada e digest fixado.
- **FR-002**: O serviço MUST acessar o OVMS por `http://ovms:8000`, nunca por `localhost` dentro do container.
- **FR-003**: O benchmark MUST usar `/v1/chat/completions`, o modelo selecionado e streaming para permitir TTFT.
- **FR-004**: O benchmark MUST reutilizar tokenizers locais por montagem somente leitura e não duplicar pesos.
- **FR-005**: Cada execução MUST gravar JSON, CSV e HTML em `harness/.agent-work/benchmarks/guidellm/<run-id>/`.
- **FR-006**: O relatório MUST distinguir throughput agregado de velocidade por requisição e registrar a origem das contagens de tokens.
- **FR-007**: O comando MUST permitir controlar modelo, prompt tokens, output tokens, concorrência e limites de execução.
- **FR-008**: O benchmark MUST falhar com código não zero quando o OVMS não estiver acessível ou a execução falhar.
- **FR-009**: A integração MUST NOT alterar as três rotas públicas do FastAPI nem adicionar GuideLLM às dependências de produção.
- **FR-010**: A documentação MUST explicar como localizar os relatórios, interpretar TTFT/ITL/latência/tokens por segundo e separar evidência de GPU de métrica do cliente.

## Acceptance Criteria

- `docker compose config -q` passa com o serviço de benchmark.
- `guidellm --version` retorna `0.7.3` no container fixado.
- Uma execução curta real com concorrência 1 produz relatórios JSON, CSV e HTML.
- O JSON identifica `qwen3-8b`, `http://ovms:8000`, `/v1/chat/completions` e o tokenizer local.
- As respostas recebidas contêm contagem de uso ou a documentação identifica claramente quando a contagem é derivada pelo tokenizer.
- Os logs do OVMS continuam sendo a evidência de dispositivo; GuideLLM não é tratado como prova de uso da GPU.

## Out of Scope

- Alterar o FastAPI para expor métricas novas.
- Prometheus, Grafana, OpenTelemetry ou armazenamento de séries temporais.
- Benchmark de longa duração, saturação ou tuning automático.
- Download ou conversão de modelos.
