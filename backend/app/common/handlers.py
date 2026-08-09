"""FastAPI exception handlers."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.exceptions import AppException
from app.common.responses import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global API exception handlers."""

    @app.exception_handler(AppException)
    async def app_exception_handler(
        _request: Request,
        exc: AppException,
    ) -> JSONResponse:
        payload = ErrorResponse(
            error=ErrorDetail(code=exc.code, message=exc.message),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=payload.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        message = "Request validation failed."
        if exc.errors():
            first_error = exc.errors()[0]
            message = first_error.get("msg", message)
        payload = ErrorResponse(
            error=ErrorDetail(code="VALIDATION_ERROR", message=message),
        )
        return JSONResponse(
            status_code=422,
            content=payload.model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        payload = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred.",
            ),
        )
        return JSONResponse(
            status_code=500,
            content=payload.model_dump(),
        )

