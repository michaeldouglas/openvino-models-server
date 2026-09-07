# Implementation Plan: Observabilidade de desempenho com GuideLLM

**Branch**: `feature/guidellm-observability` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

## Summary

Adicionar o GuideLLM como serviço opcional do Compose e um runner PowerShell permanente no harness. O serviço ficará fora do boot padrão, compartilhará a rede com o OVMS e produzirá relatórios somente na área `.agent-work`.

## Technical Context

**GuideLLM**: `v0.7.3`, image digest fixado
**Endpoint**: OVMS `http://ovms:8000/v1/chat/completions`
**Modelos**: aliases `qwen3-1.7b` e `qwen3-8b`; primeiro benchmark recomendado no 8B
**Tokenização**: tokenizer local montado de `app/models`, sem cópia de pesos
**Saídas**: `benchmarks.json`, `benchmarks.csv`, `benchmarks.html` e manifesto da execução
**Execução**: `docker compose --profile benchmark run --rm --no-deps guidellm ...`

## Design

- O profile `benchmark` impede que `docker compose up -d` execute uma carga automaticamente.
- O script resolve caminhos pelo próprio arquivo, cria um `run-id`, grava manifesto e propaga o código de saída do Compose/GuideLLM.
- A rede Docker usa DNS de serviço (`ovms`); o host não precisa publicar a porta do OVMS.
- O benchmark mede o OVMS diretamente, portanto não mede overhead do FastAPI. O contrato da API não muda.
- A imagem é fixada pelo digest publicado, enquanto o arquivo permanente registra também a tag legível.

## Validation

- Validar sintaxe do Compose e versão da imagem sem executar benchmark.
- Executar uma medição real curta se `api`/`ovms` estiverem saudáveis.
- Confirmar relatórios, código de saída, modelo, tokenizer, streaming e métricas.
- Manter qualquer relatório e log no `.agent-work`.
