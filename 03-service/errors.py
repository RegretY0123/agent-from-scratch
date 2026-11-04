import openai


class ServiceError(Exception):
    code = "INTERNAL_ERROR"
    message = "服务内部错误"
    status_code = 500

    def __init__(self, message: str | None = None):
        if message is not None:
            self.message = message
        super().__init__(self.message)


class UpstreamAuthError(ServiceError):
    code = "UPSTREAM_AUTH_FAILED"
    message = "服务端模型凭证无效，请联系管理员处理"
    status_code = 500


class UpstreamRateLimitedError(ServiceError):
    code = "UPSTREAM_RATE_LIMITED"
    message = "模型服务繁忙，请稍后重试"
    status_code = 503


class UpstreamTimeoutError(ServiceError):
    code = "UPSTREAM_TIMEOUT"
    message = "模型服务超时，请稍后重试"
    status_code = 504


class UpstreamUnavailableError(ServiceError):
    code = "UPSTREAM_UNAVAILABLE"
    message = "模型服务暂时不可用，请稍后重试"
    status_code = 503


_UPSTREAM_ERROR_MAP = (
    (openai.APITimeoutError, UpstreamTimeoutError),
    (openai.APIConnectionError, UpstreamUnavailableError),
    (openai.AuthenticationError, UpstreamAuthError),
    (openai.RateLimitError, UpstreamRateLimitedError),
    (openai.InternalServerError, UpstreamUnavailableError),
    (openai.BadRequestError, ServiceError),
)


def translate(exc: Exception) -> ServiceError:
    if isinstance(exc, ServiceError):
        return exc
    for exc_type, service_error in _UPSTREAM_ERROR_MAP:
        if isinstance(exc, exc_type):
            return service_error()
    return ServiceError()
