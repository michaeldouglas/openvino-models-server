# Feature Specification: Fast Local LLM Performance Profile

**Feature Branch**: `feature/performance-fast-profile`

**Created**: 2026-09-07

**Status**: Draft

**Input**: User description: "Faça os ajustes de performance para tornar a resposta local dos LLMs mais rápida, considerando hardware, modelos, Docker, API e benchmark."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Usar o perfil rápido local (Priority: P1)

Como desenvolvedor usando o framework em uma máquina local, quero iniciar um perfil otimizado para respostas rápidas sem carregar recursos desnecessários, para receber a primeira resposta com menor espera e comportamento previsível.

**Why this priority**: A velocidade da primeira resposta é o objetivo principal do produto e deve funcionar sem exigir que o usuário conheça detalhes do motor de inferência.

**Independent Test**: Iniciar o perfil rápido em uma instalação limpa, confirmar que o modelo rápido fica pronto e executar uma requisição de geração com sucesso.

**Acceptance Scenarios**:

1. **Given** o perfil rápido e o modelo rápido preparados, **When** o usuário inicia o ambiente, **Then** somente os recursos necessários ao perfil são carregados e o endpoint de prontidão fica disponível.
2. **Given** o ambiente pronto, **When** o usuário envia uma solicitação de geração, **Then** recebe uma resposta sem precisar configurar manualmente o dispositivo ou o scheduler.

---

### User Story 2 - Ajustar capacidade com segurança (Priority: P2)

Como operador do ambiente local, quero ajustar concorrência e capacidade de geração por configuração, para escolher entre menor latência individual e maior throughput sem alterar o código da API.

**Why this priority**: Configurações diferentes de hardware e carga exigem limites diferentes; valores fixos podem desperdiçar capacidade ou causar instabilidade.

**Independent Test**: Iniciar o ambiente com dois perfis de concorrência, executar solicitações sequenciais e concorrentes e verificar que o limite é respeitado e os resultados permanecem corretos.

**Acceptance Scenarios**:

1. **Given** um limite de concorrência configurado, **When** a carga excede o limite, **Then** o sistema rejeita ou controla a carga com um erro operacional claro, sem travar o processo.

---

### User Story 3 - Medir e comparar performance (Priority: P3)

Como mantenedor do framework, quero obter métricas reproduzíveis de inicialização e geração, para comprovar se uma alteração realmente melhora latência e throughput no hardware alvo.

**Why this priority**: Sem métricas de primeira resposta, latência total, tokens por segundo e cauda, uma otimização pode apenas parecer mais rápida.

**Independent Test**: Executar o benchmark com um conjunto fixo de prompts, aquecimento, modelo e concorrência e verificar um relatório que permita comparar duas execuções.

**Acceptance Scenarios**:

1. **Given** o ambiente pronto e um cenário de benchmark, **When** o benchmark é executado, **Then** o relatório registra configuração, sucesso/erro, latência, primeira resposta, tokens gerados e throughput.

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- O modelo rápido não está preparado ou não fica pronto: o ambiente deve indicar o motivo sem declarar sucesso prematuramente.
- O hardware tem memória insuficiente para o perfil escolhido: a inicialização deve falhar de forma diagnosticável e não esconder o erro.
- O limite configurado é maior que a capacidade suportada: a configuração deve ser rejeitada antes da execução.
- O benchmark recebe resposta parcial, timeout ou erro upstream: a execução deve registrar o caso sem contaminar as métricas de sucesso.
- O streaming entrega o primeiro token, mas falha antes do fim: o relatório deve distinguir TTFT de conclusão.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: O ambiente MUST oferecer um perfil rápido que use o modelo local de menor latência como padrão.
- **FR-002**: O perfil rápido MUST permitir que modelos opcionais de maior custo sejam excluídos do carregamento padrão.
- **FR-003**: A capacidade máxima de requisições simultâneas MUST ser configurável dentro de limites seguros e validada na inicialização.
- **FR-004**: O serviço MUST manter conexões reutilizáveis e não criar um novo cliente upstream por requisição.
- **FR-005**: O serviço MUST registrar métricas de duração total, primeira resposta, tokens gerados, tokens por segundo e erros sem registrar prompts completos.
- **FR-006**: O benchmark MUST registrar modelo, dispositivo, aquecimento, iterações, concorrência e configuração do perfil junto das métricas.
- **FR-007**: A documentação MUST indicar quando uma configuração favorece latência individual ou throughput.
- **FR-008**: Alterações de performance MUST preservar os contratos existentes de geração síncrona, assíncrona, streaming e chat compatível.

### Key Entities *(include if feature involves data)*

- **Performance Profile**: conjunto nomeado de modelo, dispositivo, limites de concorrência, cache e política de carregamento.
- **Generation Measurement**: registro de uma execução com modelo, cenário, aquecimento, latência, primeira resposta, tokens, throughput e resultado.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: O perfil rápido inicia e informa prontidão somente após o modelo configurado estar disponível.
- **SC-002**: Uma execução aquecida de geração produz métricas de TTFT, latência total e tokens por segundo em 100% das iterações válidas.
- **SC-003**: O relatório permite comparar pelo menos dois valores de concorrência e identificar o impacto em p50 e p95.
- **SC-004**: O caminho padrão do perfil rápido não carrega modelos opcionais que não participam das requisições do cenário.
- **SC-005**: Testes automatizados confirmam que a otimização não altera os contratos existentes nem os erros de limite.

## Assumptions

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right assumptions based on reasonable defaults
  chosen when the feature description did not specify certain details.
-->

- O alvo inicial é uma máquina local com Docker Desktop, WSL2 e um dispositivo Intel visível para o OVMS.
- O perfil rápido prioriza o Qwen3 1.7B; o Qwen3 8B continua disponível como perfil de qualidade ou teste separado.
- Os valores ideais de concorrência e cache serão determinados por benchmark no hardware real, não por uma promessa universal.
- Medições de performance não armazenam prompts ou respostas completas como parte do relatório persistente.
- A geração continua delegada ao OVMS; a API não passa a carregar pesos localmente.
