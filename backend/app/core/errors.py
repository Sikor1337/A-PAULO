"""Global error handling and custom exceptions."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BadRequestError(APIError):
    """Invalid operation or malformed domain request."""


class NotFoundError(APIError):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ConflictError(APIError):
    """Resource conflict (e.g., unique constraint violation)."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status.HTTP_409_CONFLICT)


class AuthenticationError(APIError):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class PermissionError(APIError):
    """Permission denied."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ValidationException(APIError):  # noqa: N818
    """Validation error."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_CONTENT)


def register_error_handlers(app: FastAPI) -> None:
    """Register global error handlers."""

    @app.exception_handler(APIError)
    async def api_exception_handler(request: Request, exc: APIError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
