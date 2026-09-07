# Chat HTML

Entre nesta pasta:

```powershell
cd app\examples\chat-html
```

Execute:

```powershell
docker compose up -d
```

Abra http://127.0.0.1:8088.

A API precisa estar rodando no Compose do projeto `app` para que o proxy
resolva o serviço `api` pela rede `app_default`.

Para parar:

```powershell
docker compose down
```
