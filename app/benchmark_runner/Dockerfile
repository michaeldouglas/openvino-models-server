FROM ghcr.io/vllm-project/guidellm:v0.7.3@sha256:e3ad2371bfa8e42f2c3d1251b62d0d9c9706c27ae2143c8c048eb5fc6aebb558

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN python -m pip install --no-cache-dir \
    fastapi==0.116.1 \
    uvicorn==0.35.0

WORKDIR /runner
COPY server.py ./server.py

EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
