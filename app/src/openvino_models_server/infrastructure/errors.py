class InferenceError(Exception):
    """Base class for safe errors raised by the inference boundary."""

    code = "upstream_failed"
    status_code = 502
    public_message = "O servidor de inferência falhou ao processar a solicitação."


class CapacityError(InferenceError):
    code = "capacity_limited"
    status_code = 429
    public_message = "A capacidade de geração está temporariamente ocupada."


class UpstreamUnavailableError(InferenceError):
    code = "upstream_unavailable"
    status_code = 503
    public_message = "O servidor de inferência está indisponível."


class UpstreamResponseError(InferenceError):
    code = "upstream_failed"
    status_code = 502
    public_message = "O servidor de inferência retornou uma resposta inválida."


class GenerationTimeoutError(InferenceError):
    code = "generation_timeout"
    status_code = 504
    public_message = "A geração excedeu o tempo limite configurado."


class NotReadyError(InferenceError):
    code = "not_ready"
    status_code = 503
    public_message = "O modelo ainda não está pronto para geração."
