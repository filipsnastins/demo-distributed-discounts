"""Global error handlers return JSON error with keys:
  - error_code
  - error_message
"""
from typing import Optional, Union

from flask import jsonify
from flask.wrappers import Response
from structlog import get_logger
from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug.http import HTTP_STATUS_CODES

from .. import db
from . import bp
from .exceptions import AppError

logger = get_logger(__name__)


def api_error_response(
    error_code: Union[int, str], error_message: Optional[str] = None, status_code: int = 500
) -> Response:
    payload = {"error_code": error_code}
    if error_message is not None:
        payload["error_message"] = error_message
    response = jsonify(payload)
    response.status_code = status_code
    return response


@bp.app_errorhandler(HTTPException)
def http_exception(exc: HTTPException) -> Response:
    error_code = HTTP_STATUS_CODES.get(exc.code, "Unknown HTTP error")
    logger.error("http_error", error_code=error_code, error_message=str(exc), status_code=exc.code)
    return api_error_response(error_code=error_code, error_message=str(exc), status_code=exc.code)


@bp.app_errorhandler(AppError)
def handle_app_error(exc: AppError):
    db.session.rollback()
    logger.error(
        "app_error",
        error_class_name=exc.__class__.__name__,
        error_code=exc.error_code,
        error_message=exc.error_message,
    )
    return api_error_response(
        error_code=exc.error_code,
        error_message=exc.error_message,
        status_code=exc.status_code,
    )


@bp.app_errorhandler(Exception)
def handle_exception(_: Exception) -> Response:
    db.session.rollback()
    logger.exception("unhandled_exception")
    error_code = HTTP_STATUS_CODES.get(InternalServerError.code)
    return api_error_response(
        error_code=error_code,
        error_message=InternalServerError.description,
        status_code=InternalServerError.code,
    )
