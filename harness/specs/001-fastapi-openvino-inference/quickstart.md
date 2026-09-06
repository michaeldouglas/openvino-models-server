# Quickstart Validation: FastAPI OpenVINO Text Inference

Este documento é um roteiro para uma fase posterior. Os comandos abaixo não
foram executados durante o planejamento.

## Prerequisites

- Docker disponível no ambiente autorizado.
- Um modelo de linguagem compatível com o fluxo OpenVINO GenAI, obtido e
  validado em etapa própria.
- Diretório do modelo disponível para montagem como somente leitura.
- Configuração de dispositivo e versão do runtime confirmadas pelas skills
  Intel aplicáveis.

## Planned configuration

Definir no arquivo de ambiente não versionado:

```text
OPENVINO_MODEL_PATH=/models/<validated-model>
OPENVINO_DEVICE=CPU
MAX_INPUT_LENGTH=<planned-limit>
REQUEST_TIMEOUT_SECONDS=<planned-timeout>
```

Os valores exatos de modelo, limite e timeout devem ser definidos na fase de
implementação após a preparação do modelo. Credenciais, quando necessárias, não
podem ser colocadas nesse arquivo versionado.

## Planned validation sequence

1. Construir a imagem a partir do `Dockerfile` com as versões registradas.
2. Iniciar o serviço conforme o `compose.yaml`, montando o modelo como somente
   leitura.
3. Consultar `GET /healthz` e confirmar `200` com `status: alive`.
4. Consultar `GET /readyz` e confirmar `200` com `status: ready` somente quando
   o modelo estiver validado e carregado.
5. Enviar `POST /v1/generate` com `{"text":"texto de teste"}` e confirmar
   `200` contendo `text`.
6. Enviar texto vazio, corpo ausente e entrada acima do limite; confirmar erro
   sem chamada ao modelo.
7. Repetir com modelo ausente ou configuração inválida; confirmar `503` e razão
   segura em `/readyz` e na operação de geração.
8. Induzir timeout controlado no ambiente de teste; confirmar `504` e log
   estruturado sem prompt ou resposta completos.
9. Verificar que o contrato implementado permanece compatível com
   `contracts/openapi.yaml`.

## Expected evidence

- Resultado separado para inicialização do runtime, carregamento do modelo,
  compilação, inferência e estado do container.
- Configuração completa do teste: modelo, versão do runtime, dispositivo,
  limites, timeout e número de solicitações.
- Nenhum claim de latência, throughput, precisão ou compatibilidade sem o
  relatório correspondente da skill Intel aplicável.
