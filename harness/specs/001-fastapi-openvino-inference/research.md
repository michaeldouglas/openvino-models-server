# Research: FastAPI OpenVINO Text Inference

**Date**: 2026-09-06
**Status**: Complete for planning; runtime validation intentionally deferred

## Decision 1: Separate the HTTP contract from model execution

**Decision**: A API terá um contrato HTTP estável e um adaptador interno para o
  mecanismo de geração. O contrato aceitará somente texto no MVP e não exporá
  objetos, caminhos ou parâmetros específicos do runtime.

**Rationale**: A constituição exige contratos FastAPI explícitos e a
especificação exige que a escolha entre execução local e servidor de modelo não
altere o contrato público. A separação também permite trocar a integração sem
forçar clientes a conhecer detalhes do modelo.

**Alternatives considered**:

- Expor diretamente a API específica do runtime: rejeitada por acoplar clientes
  a detalhes internos e dificultar testes de contrato.
- Começar com um servidor OpenVINO separado: mantido como alternativa futura,
  mas não escolhido como padrão do MVP porque o requisito atual descreve uma
  aplicação única que usa OpenVINO internamente.

## Decision 2: Use the OpenVINO GenAI text workflow as the initial integration target

**Decision**: O plano assume o fluxo textual OpenVINO GenAI para a geração. A
versão exata do runtime, o modelo, o formato final e a precisão serão fixados
somente quando as skills de documentação, instalação, conversão e hardware
forem usadas em uma fase autorizada.

**Rationale**: A necessidade é enviar texto a um modelo de linguagem, não
executar um modelo clássico de classificação ou detecção. A skill
`intel-openvino-genai-runner` cobre explicitamente fluxos textuais e de chat,
enquanto as demais skills fornecem as verificações que não podem ser inferidas
apenas pelo nome do dispositivo ou do modelo.

**Alternatives considered**:

- Usar uma API de provedor externo: rejeitada porque o requisito pede OpenVINO
  internamente e a constituição prioriza a execução local/containerizada.
- Usar somente o runtime clássico de inferência: não escolhido para o contrato
  inicial de geração de texto, embora possa ser usado por uma integração futura
  quando o modelo exigir esse caminho.

## Decision 3: Make model and device runtime configuration

**Decision**: O modelo será apontado por configuração de ambiente e fornecido
por volume somente leitura. O dispositivo será selecionável por configuração,
com `CPU` como perfil inicial conservador do plano; `AUTO`, `MULTI` ou outro
dispositivo só será adotado após evidência correspondente.

**Rationale**: Não existe ainda um modelo nem relatório do hardware no
repositório. A skill de hardware determina que detecção de dispositivo não
prova compatibilidade, precisão ou desempenho. Configuração externa preserva
artefatos originais e permite validar o mesmo contrato em ambientes distintos.

**Alternatives considered**:

- Embutir o modelo na imagem: rejeitada por aumentar o acoplamento, dificultar
  atualização e contrariar a preservação de artefatos fornecidos.
- Escolher automaticamente o melhor dispositivo sem evidência: rejeitada por
  transformar uma preferência em uma afirmação de compatibilidade.

## Decision 4: Define liveness and readiness separately

**Decision**: A API terá um estado de saúde do processo e um estado de prontidão
que depende da configuração e disponibilidade do modelo. Falhas de prontidão
serão reportadas com razões seguras e estáveis.

**Rationale**: O serviço pode estar executando sem conseguir gerar texto. A
separação permite diagnóstico operacional e atende diretamente aos cenários de
modelo ausente ou falha de configuração.

**Alternatives considered**:

- Um único endpoint de saúde: rejeitado porque mistura processo vivo com
  capacidade funcional.
- Expor exceções e stack traces para diagnosticar: rejeitado pela constituição
  e pelo requisito de não revelar detalhes internos.

## Decision 5: Defer installation, conversion, optimization, inference and benchmarking

**Decision**: Este plano descreve pontos de integração e critérios de validação,
mas não executa scripts das skills Intel nem cria artefatos de modelo. Cada
atividade futura terá seu próprio plano, confirmação quando exigida e resultado
separado: instalação, conversão, compilação/inferência, otimização e benchmark.

**Rationale**: Essa é uma restrição explícita do solicitante. Também preserva as
fronteiras das skills: sucesso de instalação não prova compilação; compilação não
prova desempenho; otimização não prova equivalência de qualidade.

**Alternatives considered**:

- Executar uma sondagem ou benchmark para preencher o plano: rejeitado porque a
  fase atual é exclusivamente de estruturação.
- Escolher versões ou tags atuais sem validação: rejeitado por risco de afirmar
  compatibilidade sem documentação e evidência de ambiente.

## Resolved Planning Questions

- **Arquitetura do MVP**: serviço único com adaptador interno OpenVINO GenAI.
- **Persistência**: nenhuma persistência de negócio; modelo em volume de leitura.
- **Contrato inicial**: uma entrada textual, resposta não contínua e erros
  estruturados.
- **Ambiente-alvo**: container Linux para execução local ou controlada.
- **Escopo de execução deste comando**: somente design; nenhum runtime será
  instalado ou iniciado.
