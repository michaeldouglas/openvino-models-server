# Feature Specification: Seleção entre modelos Qwen

**Feature Branch**: `feature/multi-model-qwen-selection`
**Created**: 2026-09-06
**Status**: Ready for implementation
**Input**: User description: manter Qwen 1.7B e Qwen 8B disponíveis e permitir escolher o modelo em cada geração.

## User Scenarios & Testing

### User Story 1 - Escolher o modelo por requisição (Priority: P1)

Como consumidor da API, quero informar um modelo permitido na requisição para escolher entre o Qwen3-1.7B e o Qwen3-8B, sem alterar outras requisições.

**Why this priority**: É o valor principal da feature e permite comparar capacidade, latência e consumo sem trocar manualmente a configuração do serviço.

**Independent Test**: Com dois servables disponíveis, enviar a mesma solicitação para cada nome permitido e verificar que cada resposta informa o modelo escolhido.

**Acceptance Scenarios**:

1. **Given** os dois modelos estão disponíveis, **When** o cliente envia `model` igual a um modelo permitido, **Then** a API encaminha esse nome ao OVMS e devolve o mesmo modelo na resposta.
2. **Given** nenhuma seleção foi enviada, **When** o cliente chama qualquer rota de geração, **Then** a API usa o modelo padrão configurado.
3. **Given** duas requisições simultâneas escolhem modelos diferentes, **When** ambas são processadas, **Then** cada resposta permanece associada ao seu próprio modelo.

### User Story 2 - Consultar modelos disponíveis (Priority: P2)

Como operador, quero consultar o catálogo e o estado dos modelos para saber quais podem receber tráfego.

**Why this priority**: Evita tentativas cegas e torna readiness e falhas de carregamento observáveis.

**Independent Test**: Consultar a rota de modelos com OVMS ativo, indisponível e com apenas um modelo carregado, verificando estados e modelo padrão.

**Acceptance Scenarios**:

1. **Given** o upstream responde com os servables carregados, **When** o operador consulta o catálogo, **Then** cada modelo configurado aparece com estado `ready` ou `unavailable` e apenas um é marcado como padrão.
2. **Given** o OVMS está indisponível, **When** o operador consulta o catálogo, **Then** a API retorna estados indisponíveis sem expor stack trace ou credenciais.

### User Story 3 - Preparar os dois artefatos sem baixar no boot (Priority: P3)

Como operador local, quero preparar os modelos uma vez em armazenamento persistente e iniciar a stack reutilizando os artefatos válidos.

**Why this priority**: Reduz falhas de rede e torna o início do serviço previsível, preservando o modelo atual como fallback.

**Independent Test**: Executar o comando de preparação duas vezes e verificar que a segunda execução reutiliza artefatos completos; iniciar o Compose sem exigir novo download.

**Acceptance Scenarios**:

1. **Given** o repositório contém um modelo completo, **When** a preparação é executada novamente, **Then** o modelo não é baixado novamente.
2. **Given** o segundo modelo ainda não foi preparado, **When** o Compose é iniciado, **Then** a operação falha de forma explícita ou mantém somente o modelo pronto, sem alegar que o segundo está disponível.

## Edge Cases

- Um nome de modelo desconhecido ou não permitido deve retornar erro de modelo não encontrado sem ser encaminhado ao OVMS.
- Um modelo configurado, mas ainda não carregado, deve retornar indisponibilidade controlada.
- A resposta do OVMS pode informar um modelo diferente do solicitado; a API deve rejeitar a inconsistência em vez de mascará-la.
- O catálogo pode conter duplicidades ou IDs vazios vindos da configuração; a aplicação deve rejeitar configuração inválida ao iniciar.
- O modelo grande pode não caber na memória compartilhada da GPU quando ambos estiverem carregados; a documentação deve exigir teste real e limitar concorrência inicial.
- A ausência de `config.json` ou de `graph.pbtxt` deve ser reportada como falha de preparação, sem download automático durante o boot.

## Requirements

### Functional Requirements

- **FR-001**: O sistema MUST manter uma lista configurável de modelos permitidos e um modelo padrão.
- **FR-002**: As três rotas de geração MUST aceitar um identificador opcional de modelo e usar o padrão quando ele não for enviado.
- **FR-003**: A API MUST encaminhar o identificador selecionado ao OVMS e retornar o identificador efetivamente usado.
- **FR-004**: A seleção de um modelo MUST ser isolada por requisição e não modificar uma variável global compartilhada.
- **FR-005**: A API MUST expor um catálogo operacional com os modelos configurados, estado de disponibilidade e indicação do padrão.
- **FR-006**: Nomes fora do catálogo MUST ser rejeitados antes da chamada ao upstream.
- **FR-007**: O OVMS MUST usar uma configuração capaz de servir múltiplos modelos no mesmo processo, com GPU explicitamente configurada em cada grafo/modelo.
- **FR-008**: A preparação MUST armazenar os artefatos em `app/models`, ser idempotente e preservar os artefatos do Qwen3-1.7B durante a preparação do Qwen3-8B.
- **FR-009**: O sistema MUST continuar funcionando com o modelo padrão pronto mesmo quando um modelo opcional estiver indisponível, desde que essa condição seja indicada no catálogo.
- **FR-010**: A configuração MUST limitar a concorrência inicial e não prometer desempenho ou compatibilidade do Qwen3-8B antes da validação real na GPU.
- **FR-011**: Os testes MUST cobrir seleção, fallback, modelo desconhecido, catálogo indisponível, propagação do nome ao OVMS e isolamento entre requisições.
- **FR-012**: A documentação MUST registrar modelo, revisão, precisão, licença, requisitos de preparação e limitações de memória.

### Key Entities

- **ModelDefinition**: Identificador público permitido, origem, revisão, precisão, caminho persistente e indicação do modelo padrão.
- **ModelStatus**: Identificador, estado (`ready` ou `unavailable`), motivo seguro e indicação de padrão.
- **GenerationRequest**: Texto, parâmetros de geração e seleção opcional de modelo.

## Success Criteria

### Measurable Outcomes

- **SC-001**: As três rotas de geração aceitam os dois identificadores configurados sem alterar o contrato das requisições que omitem `model`.
- **SC-002**: Uma seleção desconhecida é rejeitada em 100% dos testes sem gerar chamada ao OVMS.
- **SC-003**: O catálogo informa corretamente o estado de cada modelo em cenários de upstream saudável e indisponível.
- **SC-004**: A preparação repetida não cria cópias duplicadas nem substitui um artefato válido já existente.
- **SC-005**: A validação sem GPU e sem download passa; a aceitação com o Qwen3-8B só é marcada como concluída após evidência real de carga e geração na GPU.

## Assumptions

- Os dois modelos são artefatos OpenVINO pré-preparados e ficam fora do Git em `app/models`.
- O primeiro modelo permanece `OpenVINO/Qwen3-1.7B-int4-ov`; o segundo é `OpenVINO/Qwen3-8B-int4-ov`.
- O modelo padrão inicial continua sendo o 1.7B para preservar o comportamento atual.
- O cliente pode escolher somente IDs registrados; download dinâmico e autenticação administrativa são escopo posterior.
- O Compose usa a imagem versionada atual do OVMS e o mesmo caminho de GPU WSL2 já validado para o modelo atual.
- Qualidade relativa e desempenho do 8B serão determinados por benchmark controlado, não por inferência a partir do número de parâmetros.
