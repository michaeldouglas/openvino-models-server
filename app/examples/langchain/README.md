# LangChain com o runtime local

Instale o extra opcional no ambiente da aplicação consumidora:

```powershell
python -m pip install "local-llm[langchain]"
```

O cliente local usa o contrato OpenAI-compatível. Provedores pagos continuam
sendo instanciados separadamente pelo consumidor; não existe fallback remoto
implícito dentro do `local-llm`.

```python
from langchain_openai import ChatOpenAI

local = ChatOpenAI(
    model="qwen3-1.7b",
    base_url="http://127.0.0.1:8000/v1",
    api_key="local-not-used",
    temperature=0.2,
    max_tokens=64,
)

answer = local.invoke("Explique OpenVINO em uma frase.")
print(answer.content)
```

Para usar um provedor pago, crie o cliente oficial correspondente e escolha
explicitamente qual runnable executar. Nunca coloque uma chave paga no `.env`
do runtime local só para selecionar o alias local.
