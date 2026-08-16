"""FastAPI exception handlers."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.exceptions import AppException
from app.common.responses import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


def _json_error(status_code: int, code: str, message: str) -> JSONResponse:
    payload = ErrorResponse(error=ErrorDetail(code=code, message=message))
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Register global API exception handlers."""

    @app.exception_handler(AppException)
    async def app_exception_handler(
        _request: Request,
        exc: AppException,
    ) -> JSONResponse:
        return _json_error(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        message = "Request validation failed."
        if exc.errors():
            first_error = exc.errors()[0]
            message = first_error.get("msg", message)
        return _json_error(422, "VALIDATION_ERROR", message)

    @app.exception_handler(ResponseValidationError)
    async def response_validation_exception_handler(
        _request: Request,
        exc: ResponseValidationError,
    ) -> JSONResponse:
        logger.exception("Response validation failed")
        message = "The server produced an invalid response."
        if exc.errors():
            first_error = exc.errors()[0]
            message = first_error.get("msg", message)
        return _json_error(500, "RESPONSE_VALIDATION_ERROR", message)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, str):
            message = detail
        elif isinstance(detail, list) and detail:
            message = str(detail[0])
        else:
            message = "Request failed."
        code = "UNAUTHORIZED" if exc.status_code == 401 else "REQUEST_FAILED"
        return _json_error(exc.status_code, code, message)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return _json_error(500, "INTERNAL_ERROR", "An unexpected error occurred.")

