from typing import Any

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class AccountNotFound(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "ACCOUNT_NOT_FOUND"


class InsufficientBalance(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "INSUFFICIENT_BALANCE"


class DuplicateTransaction(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "DUPLICATE_TRANSACTION"


def _envelope(code: str, message: str, details: dict[str, Any]) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details}}


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(exc.code, exc.message, exc.details),
    )


async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_envelope(
            "VALIDATION_ERROR", "Invalid request data", {"errors": jsonable_encoder(exc.errors())}
        ),
    )
