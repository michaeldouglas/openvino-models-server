# Feature Specification: Execução de benchmarks pela API

**Feature Branch**: `feature/api-benchmark-route`
**Created**: 2026-09-07
**Status**: Implemented and validated locally
**Input**: Permitir que a API solicite benchmarks do modelo servido pelo OVMS e grave os relatórios em uma pasta local ignorada pelo Git.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Solicitar uma medição sem bloquear a API (Priority: P1)

Como operador, quero solicitar uma medição de desempenho pela API e receber um
identificador imediatamente, para que uma execução demorada não bloqueie a
requisição HTTP nem as rotas de geração.

**Independent Test**: Enviar uma solicitação válida, receber um identificador
com estado inicial e confirmar que a execução pode evoluir até concluída ou
falha sem alterar uma geração em andamento.

### User Story 2 - Consultar execução e relatórios (Priority: P1)

Como operador, quero consultar o estado e obter os relatórios de uma execução,
para analisar tokens, latência, TTFT, concorrência e falhas sem acessar o
container diretamente.

**Independent Test**: Criar uma execução controlada, consultar seu estado e
obter os formatos de relatório disponíveis quando ela terminar.

### User Story 3 - Executar medições de forma segura e repetível (Priority: P1)

Como responsável pela operação, quero que os parâmetros sejam limitados, os
modelos sejam escolhidos de um catálogo conhecido e cada execução tenha uma
pasta exclusiva, para evitar comandos arbitrários, colisões e acúmulo
incontrolado de trabalho.

**Independent Test**: Rejeitar modelo ou limite inválido, impedir concorrência
acima da capacidade configurada e confirmar que duas execuções válidas não
compartilham arquivos de resultado.

### User Story 4 - Preservar o caminho existente de geração (Priority: P2)

Como consumidor da API, quero continuar usando as três rotas de geração sem
alteração de contrato enquanto um benchmark é executado, para que a
observabilidade seja adicional e não quebre o uso normal do serviço.

**Independent Test**: Executar as verificações das rotas de geração e uma
solicitação de benchmark no mesmo ambiente, confirmando que ambas mantêm seus
contratos e limites.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST aceitar uma solicitação de benchmark com modelo,
  tamanho de entrada, tamanho de saída, concorrência, quantidade máxima de
  requisições e duração opcional.
- **FR-002**: Uma solicitação válida MUST retornar um identificador único e um
  estado sem aguardar a conclusão da medição.
- **FR-003**: O sistema MUST expor o estado, a contagem de requisições e os
  caminhos lógicos dos relatórios por identificador.
- **FR-004**: Uma execução concluída MUST disponibilizar JSON, CSV e HTML quando
  o executor de benchmark suportar esses formatos.
- **FR-005**: Os resultados MUST ser gravados em armazenamento local
  configurável, inicialmente `app/results/`, e MUST ser ignorados pelo Git.
- **FR-006**: O catálogo de modelos e todos os limites MUST ser controlados por
  configuração, sem aceitar comandos, URLs, caminhos ou nomes arbitrários do
  cliente.
- **FR-007**: O sistema MUST limitar a quantidade de execuções simultâneas e
  informar capacidade indisponível sem criar uma fila ilimitada.
- **FR-008**: Falhas do executor, indisponibilidade do OVMS e timeouts MUST
  resultar em estado de falha e mensagem segura, sem stack trace, segredo ou
  prompt completo.
- **FR-009**: O serviço de benchmark MUST executar isolado do processo da API e
  não MUST exigir acesso do FastAPI ao socket ou daemon do Docker.
- **FR-010**: As rotas de geração existentes, seus esquemas e as dependências
  de produção MUST permanecer compatíveis.

### Key Entities *(include if feature involves data)*

- **BenchmarkJob**: identificador, modelo, parâmetros validados, estado,
  timestamps, contagens, erro público e arquivos produzidos.
- **BenchmarkRequest**: entrada operacional limitada e validada para iniciar
  uma medição.
- **BenchmarkReport**: arquivo produzido em formato permitido e associado a
  exatamente um `BenchmarkJob`.

## Success Criteria *(mandatory)*

- **SC-001**: Uma solicitação válida recebe identificador e estado inicial em
  até 1 segundo, sem esperar a geração terminar.
- **SC-002**: Em uma execução controlada concluída, 100% dos relatórios
  anunciados podem ser obtidos pelo identificador correto.
- **SC-003**: Solicitações com modelo, caminho, comando ou limite fora da
  configuração são rejeitadas antes de iniciar trabalho externo.
- **SC-004**: Duas execuções válidas simultâneas nunca sobrescrevem arquivos
  uma da outra e a capacidade configurada é respeitada.
- **SC-005**: As três rotas de geração existentes continuam passando seus
  testes automatizados e mantendo seus códigos de resposta.
- **SC-006**: Um erro do executor aparece como estado de falha sem expor
  credenciais, stack trace ou o texto completo enviado ao modelo.

## Assumptions

- O executor de benchmark continua sendo o GuideLLM já fixado e acessa o OVMS
  pela rede interna do Compose.
- A primeira versão usa estado em memória no serviço executor; reinicialização
  não promete recuperar jobs ativos, mas os arquivos já concluídos permanecem
  no armazenamento configurado.
- O acesso às rotas de benchmark será local/interno nesta primeira versão; uma
  camada de autenticação dedicada fica fora do escopo atual.
- A API não serve arquivos arbitrários do sistema; somente os formatos e
  identificadores gerados pelo próprio executor são permitidos.

## Out of Scope

- Download, conversão ou troca de modelos pela API.
- Acesso ao Docker socket pelo FastAPI.
- Fila persistente, Redis, Celery, banco de dados ou execução distribuída.
- Prometheus, Grafana ou armazenamento histórico de séries temporais.
