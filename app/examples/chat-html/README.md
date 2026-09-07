# Chat HTML

A partir de `app/`, execute o Compose principal com o perfil do exemplo:

```powershell
cd runtime\deployment
docker compose --profile chat-example up -d --build
```

Abra http://127.0.0.1:8088.

O mesmo Compose inicia a API, o OVMS e o serviço estático do exemplo na mesma
rede. O proxy do Nginx encaminha `/api/*` para a API local.

Para parar:

```powershell
docker compose down
```
