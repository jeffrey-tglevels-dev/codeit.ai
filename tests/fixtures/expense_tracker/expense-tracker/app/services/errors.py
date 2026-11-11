class ServiceError(Exception):
    """A business-rule failure; routes turn it into an HTTP error."""

    status_code = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class Invalid(ServiceError):
    status_code = 400


class NotFound(ServiceError):
    status_code = 404


class Conflict(ServiceError):
    status_code = 409
