# Research: Seleção entre modelos Qwen

## Decisions

### OVMS em modo de configuração múltipla

- **Decision**: usar `config.json` para dois servables no mesmo processo OVMS.
- **Rationale**: o modo de CLI com `--source_model` é adequado para um único modelo; a documentação do OVMS exige configuração JSON para servir múltiplos modelos e permite reload de configuração em runtime.
- **Evidence**: `https://docs.openvino.ai/2026/model-server/ovms_docs_serving_model.html` e `https://github.com/openvinotoolkit/model_server/blob/main/docs/online_config_changes.md`.

### Seleção por requisição

- **Decision**: o cliente envia um alias permitido em `model`; a ausência usa o 1.7B como padrão.
- **Rationale**: evita estado global mutável e mantém requisições independentes. O alias é traduzido para o nome do servable no catálogo interno.
- **Rejected**: trocar uma variável global de modelo a cada chamada, pois cria corrida entre requisições e não isola respostas.

### Modelos

- `qwen3-1.7b`: `OpenVINO/Qwen3-1.7B-int4-ov`, revisão `main`, INT4, Apache-2.0. Artefato local previamente validado no OVMS/GPU.
- `qwen3-8b`: `OpenVINO/Qwen3-8B-int4-ov`, revisão `main`, INT4, Apache-2.0. Artefato oficial de aproximadamente 4,88 GB; compatível com OpenVINO 2026.0+ segundo o model card.
- **Evidence**: `https://huggingface.co/OpenVINO/Qwen3-8B-int4-ov` e `https://docs.openvino.ai/2026/model-server/ovms_docs_llm_quickstart.html`.

### Memória e aceitação

- **Decision**: começar com `max_num_seqs=1` para o 8B e manter o modelo atual como fallback.
- **Rationale**: a GPU Arc 140V é integrada e usa memória compartilhada; o Docker Desktop foi observado com aproximadamente 15,4 GiB. O tamanho do arquivo não equivale ao consumo de execução.
- **Unresolved**: carga simultânea dos dois modelos, TTFT e tokens/s precisam de medição real no container. A configuração escrita não será tratada como prova de compatibilidade.

### Preparação

- **Decision**: disponibilizar script idempotente de preparação que usa o modo `--pull`/configuração do OVMS e grava em `app/models`; o Compose não baixa modelos no boot.
- **Rationale**: separa rede/conversão da inicialização e preserva artefatos válidos.
- **Security**: IDs e revisões são allowlist no script; tokens do Hugging Face entram apenas por variável de processo quando necessários.

## Alternatives considered

- **Dois containers OVMS**: rejeitado para esta feature por duplicar processos e complicar memória/conexão; um OVMS já suporta múltiplos servables.
- **Ollama ou outro runtime**: fora do escopo; a arquitetura do projeto permanece FastAPI + OVMS/OpenVINO.
- **Download pela rota HTTP**: reservado para uma feature futura; o gerenciamento assíncrono de downloads e autenticação administrativa não é necessário para a seleção inicial.
