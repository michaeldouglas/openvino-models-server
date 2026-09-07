class InferenceError(Exception):
    """Base class for safe errors raised by the inference boundary."""

    code = "upstream_failed"
    status_code = 502
    public_message = "O servidor de inferência falhou ao processar a solicitação."


class CapacityError(InferenceError):
    code = "capacity_limited"
    status_code = 429
    public_message = "A capacidade de geração está temporariamente ocupada."


class ModelNotFoundError(InferenceError):
    code = "model_not_found"
    status_code = 404
    public_message = "O modelo solicitado não está no catálogo permitido."


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


class BenchmarkUnavailableError(InferenceError):
    code = "benchmark_unavailable"
    status_code = 503
    public_message = "O executor de benchmark está indisponível."


class BenchmarkCapacityError(InferenceError):
    code = "benchmark_capacity"
    status_code = 429
    public_message = "Já existe um benchmark em execução."


class BenchmarkNotFoundError(InferenceError):
    code = "benchmark_not_found"
    status_code = 404
    public_message = "A execução de benchmark não foi encontrada."


class BenchmarkNotReadyError(InferenceError):
    code = "benchmark_not_ready"
    status_code = 409
    public_message = "O relatório do benchmark ainda não está pronto."


class BenchmarkFailedError(InferenceError):
    code = "benchmark_failed"
    status_code = 502
    public_message = "O executor não conseguiu concluir o benchmark."
