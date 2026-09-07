# Feature Specification: Framework local de LLMs

**Feature Branch**: `feature/performance-and-layout`

**Created**: 2026-09-07

**Status**: Implemented

**Input**: Transformar o servidor OpenVINO em um framework instalável para execução local de LLMs, com API compatível com OpenAI, integração opcional com LangChain, gerenciamento de modelos, streaming, configuração de desempenho e separação física entre API, runtime e benchmark.

## User Scenarios & Testing

### User Story 1 - Instalar e executar um modelo local (Priority: P1)

Como desenvolvedor, quero instalar o framework e iniciar um modelo local por comando para usar inferência na minha própria máquina sem depender de um provedor pago.

**Why this priority**: É o valor principal do produto e deve funcionar antes das integrações opcionais.

**Independent Test**: Em uma máquina com o runtime e um modelo compatível, instalar o pacote, listar um modelo, iniciá-lo e obter uma resposta de texto.

**Acceptance Scenarios**:

1. **Given** que o runtime local está instalado, **When** o usuário lista os modelos disponíveis, **Then** recebe aliases, precisão, dispositivo e requisitos do modelo.
2. **Given** que um modelo compatível foi preparado, **When** o usuário inicia o serviço local, **Then** o serviço informa estado de prontidão e aceita uma geração normal e uma geração em streaming.
3. **Given** que o usuário escolhe um modelo por requisição, **When** envia a solicitação, **Then** apenas aquela requisição usa o modelo selecionado.

### User Story 2 - Usar o runtime em clientes compatíveis (Priority: P2)

Como desenvolvedor, quero usar o endpoint local com clientes que já falam o formato OpenAI Chat Completions, incluindo LangChain, sem escrever um adaptador específico para cada aplicação.

**Why this priority**: A compatibilidade reduz a barreira de adoção e permite usar o framework em agentes e aplicações existentes.

**Independent Test**: Apontar um cliente OpenAI-compatible e um cliente LangChain para o endpoint local e validar resposta, streaming, seleção de modelo e erros documentados.

**Acceptance Scenarios**:

1. **Given** um endpoint local pronto, **When** o cliente envia mensagens no contrato Chat Completions, **Then** recebe uma resposta compatível com o formato esperado pelo cliente.
2. **Given** que o cliente solicita streaming, **When** o modelo gera tokens, **Then** os deltas são entregues incrementalmente e a conclusão é sinalizada.
3. **Given** uma opção de modelo inexistente ou uma requisição inválida, **When** o cliente chama o endpoint, **Then** recebe erro estruturado sem stack trace ou segredo.

### User Story 3 - Usar modelos locais ao lado de provedores remotos (Priority: P3)

Como desenvolvedor, quero usar o modelo local pelo mesmo ecossistema de clientes em que já uso OpenAI e outros provedores pagos, escolhendo explicitamente entre eles por caso de uso.

**Why this priority**: Permite adoção gradual e fallback explícito sem obrigar o framework a enviar dados locais para a nuvem.

**Independent Test**: Usar o endpoint local com um alias local e, separadamente, um cliente do provedor remoto, verificando que o framework local não envia dados para a nuvem sem uma ação explícita da aplicação.

**Acceptance Scenarios**:

1. **Given** um cliente configurado para o endpoint local, **When** o usuário escolhe um alias local, **Then** a requisição é encaminhada somente ao runtime local.
2. **Given** que o usuário também possui um cliente remoto, **When** escolhe esse cliente na própria aplicação, **Then** a decisão fica explícita e independente do runtime local.

### User Story 4 - Medir e comparar o runtime (Priority: P3)

Como mantenedor, quero executar benchmarks separados do runtime de produção para comparar modelo, dispositivo, concorrência, streaming e configurações sem misturar artefatos de benchmark com o código da API.

**Why this priority**: Desempenho precisa ser verificável e não pode depender de alterações manuais no serviço principal.

**Independent Test**: Executar uma medição contra um modelo pronto, gerar relatórios JSON/CSV/HTML e confirmar que eles ficam na área de benchmark.

**Acceptance Scenarios**:

1. **Given** um modelo pronto e o serviço ativo, **When** o usuário executa um benchmark, **Then** recebe métricas de sucesso, latência, TTFT, tokens/s e concorrência.
2. **Given** uma execução inválida ou sem resposta do runtime, **When** o benchmark termina, **Then** retorna falha e não apresenta um relatório de erro como desempenho válido.

### Edge Cases

- O modelo solicitado não existe, está incompleto ou não suporta o dispositivo.
- O dispositivo GPU não está disponível, mas o usuário não autorizou fallback para CPU.
- O endpoint recebe uma requisição acima do limite de entrada ou saída.
- Um cliente desconecta durante o streaming.
- O runtime local está ocupado com outra execução e deve aplicar limite de concorrência sem perder respostas em andamento.
- O download do modelo é interrompido ou o checksum não corresponde ao manifesto.
- O benchmark é executado sem modelo preparado ou com zero requisições válidas.
- Um provedor remoto está configurado sem credencial; a chave nunca deve ser registrada em logs ou arquivos versionados.

## Requirements

### Functional Requirements

- **FR-001**: O framework MUST expor uma interface de núcleo independente de FastAPI, LangChain e de um provedor específico.
- **FR-002**: O framework MUST permitir instalar o pacote sem embutir pesos de modelos no pacote distribuível.
- **FR-003**: O framework MUST oferecer comandos para listar, preparar, inspecionar e selecionar modelos por alias.
- **FR-004**: Cada manifesto de modelo MUST registrar origem, revisão, precisão, licença, dispositivos suportados e integridade do artefato.
- **FR-005**: O runtime MUST suportar seleção de modelo por requisição sem alterar globalmente requisições concorrentes.
- **FR-006**: O servidor MUST expor endpoints de prontidão e de modelos e um contrato de chat compatível com OpenAI, incluindo streaming.
- **FR-007**: O servidor MUST limitar entrada, saída e concorrência por configuração documentada e retornar erros estruturados.
- **FR-008**: O framework MUST permitir configurar dispositivo, limites de tokens, temperatura, cache e parâmetros de agendamento suportados pelo runtime.
- **FR-009**: O runtime local MUST NOT encaminhar payload para provedores remotos por falha ou indisponibilidade; qualquer uso remoto MUST ser uma decisão explícita do cliente ou de uma integração opt-in, com credenciais fora do código, imagens e logs.
- **FR-010**: A integração LangChain MUST ser opcional e não pode ser uma dependência obrigatória do núcleo.
- **FR-011**: O benchmark MUST ficar fisicamente separado do runtime da API e seus resultados MUST ficar em uma área pertencente ao benchmark.
- **FR-012**: O benchmark MUST medir pelo menos sucesso/erro, latência, TTFT, tokens por segundo e concorrência em cargas reproduzíveis.
- **FR-013**: O projeto MUST ter testes unitários para contratos e adaptadores, testes de API para sucesso/validação/erro/streaming e um smoke test do caminho containerizado.
- **FR-014**: A documentação MUST incluir instalação, preparação do modelo, execução local, uso com cliente OpenAI-compatible, uso com LangChain, benchmark e limitações de dispositivo.

### Key Entities

- **ModelManifest**: identidade, origem, revisão, licença, precisão, artefatos, dispositivo e requisitos de um modelo instalável.
- **ModelAlias**: nome estável usado pelo usuário para selecionar um modelo ou provedor.
- **ChatRequest**: mensagens, modelo, limites de geração, temperatura, streaming e opções compatíveis.
- **ChatResponse/ChatChunk**: resposta completa ou delta incremental, motivo de parada, uso de tokens e erro estruturado quando aplicável.
- **ProviderConfig**: configuração não secreta de um runtime local ou remoto; segredos são injetados somente em tempo de execução.
- **BenchmarkRun**: parâmetros, estado, métricas e arquivos gerados por uma execução de medição.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Um novo usuário consegue instalar o pacote, listar um modelo preparado e iniciar uma geração local seguindo o quickstart em até 10 minutos.
- **SC-002**: O fluxo local retorna a prontidão do modelo e uma resposta de texto sem exigir conta ou chave de provedor remoto.
- **SC-003**: O streaming entrega o primeiro delta dentro da latência observada no benchmark de referência, com p95 documentado por modelo e configuração.
- **SC-004**: Pelo menos 95% das requisições válidas de uma carga de referência são concluídas sem erro quando o dispositivo e o modelo estão prontos.
- **SC-005**: Um cliente OpenAI-compatible e uma aplicação LangChain conseguem usar o modelo local sem código de transporte específico do runtime.
- **SC-006**: Os relatórios de benchmark ficam separados do pacote da API e permitem reproduzir a comparação de modelo, dispositivo e concorrência.
- **SC-007**: Nenhum teste ou fluxo padrão envia dados a um provedor remoto sem uma configuração explícita de fallback.

## Assumptions

- A primeira versão terá como foco Python, Windows/WSL2 e Linux com dispositivos Intel suportados; outras plataformas serão documentadas como futuras.
- O runtime OVMS continuará sendo uma opção de servidor e o modo biblioteca direta poderá ser introduzido sem mudar os contratos do núcleo.
- Modelos são baixados ou preparados separadamente, com respeito às licenças e sem entrar no pacote Python ou no Git.
- A primeira integração LangChain usará o contrato OpenAI-compatible; provedores pagos continuarão sendo selecionados diretamente pelo cliente LangChain ou SDK correspondente.
- O encaminhamento automático para nuvem ficará fora do escopo e a autenticação do servidor local ficará fora do escopo da primeira versão.
- A reorganização deve preservar as rotas atuais durante a migração, salvo a adição explícita do contrato Chat Completions.
