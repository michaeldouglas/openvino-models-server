# Data Model: Seleção entre modelos Qwen

## ModelDefinition

Representa um modelo permitido pela aplicação.

| Campo | Tipo | Regras |
|---|---|---|
| `id` | string | Alias público não vazio e único, usado nas requisições |
| `servable_name` | string | Nome encaminhado ao OVMS |
| `source_model` | string | Referência registrada do artefato, nunca recebida livremente do cliente |
| `revision` | string | Revisão documentada do artefato |
| `precision` | string | Precisão preparada, inicialmente `INT4` |
| `default` | boolean | Exatamente um modelo é padrão |

## ModelStatus

Estado observado no upstream para uma definição conhecida.

| Campo | Tipo | Regras |
|---|---|---|
| `id` | string | Alias do catálogo |
| `status` | enum | `ready` ou `unavailable` |
| `default` | boolean | Copiado da definição |
| `reason` | string/null | Mensagem segura, sem URL interna, token ou stack trace |

## GenerationRequest

Extensão compatível do contrato atual:

| Campo | Tipo | Regras |
|---|---|---|
| `model` | string/null | Opcional; deve ser um alias do catálogo |
| `text` | string | Não vazio e dentro do limite existente |
| `max_tokens` | integer/null | Mantém limites atuais |
| `temperature` | number/null | Mantém limites atuais |

## State transitions

```text
configured -> ready
configured -> unavailable
ready -> unavailable (upstream/model unload)
unavailable -> ready (model reload/preparation)
```

O estado não é persistido pela API; ele é consultado no OVMS. Os artefatos são persistentes em `app/models` e não participam da limpeza de testes.
