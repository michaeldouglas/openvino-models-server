# Quickstart: dois modelos Qwen

## Preparar os artefatos

No PowerShell, a partir de `app`:

```powershell
.\scripts\prepare-models.ps1
```

O script prepara ou reutiliza `OpenVINO/Qwen3-1.7B-int4-ov` e `OpenVINO/Qwen3-8B-int4-ov`.

Os artefatos são gravados em `app/models`, que é persistente e ignorado pelo Git. A preparação exige rede e, se o repositório solicitar, autenticação do Hugging Face em variável temporária. Não coloque o token em `.env` versionado.

## Iniciar

```powershell
docker compose up -d --build
docker compose ps
```

O Compose não faz download durante o boot. Se o repositório de modelos não estiver preparado, o OVMS deve reportar a falha; nesse caso, execute o script de preparação e tente novamente.

## Escolher o modelo

Sem seleção, o padrão é o 1.7B:

```powershell
curl.exe -X POST http://127.0.0.1:8000/v1/generate/sync `
  -H "Content-Type: application/json" `
  -d '{"text":"Explique OpenVINO em poucas palavras."}'
```

Para o modelo maior:

```powershell
curl.exe -X POST http://127.0.0.1:8000/v1/generate/sync `
  -H "Content-Type: application/json" `
  -d '{"model":"qwen3-8b","text":"Explique OpenVINO em poucas palavras.","max_tokens":64}'
```

O campo `model` também funciona nas rotas `/v1/generate/async` e `/v1/generate/stream`.

## Consultar estados

```powershell
curl.exe http://127.0.0.1:8000/v1/models
curl.exe http://127.0.0.1:8000/readyz
```

`/readyz` só fica pronto quando o modelo padrão está disponível. O catálogo mostra separadamente se o 8B ainda não foi carregado.

## Aceitação

Valide os testes sem GPU e, separadamente, a geração real dos dois modelos. O 8B não deve ser considerado aceito apenas porque aparece no catálogo: registre logs do OVMS, `target_device=GPU`, readiness, TTFT, latência, tokens/s e uso de memória observável.
