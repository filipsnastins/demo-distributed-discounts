"""Global error handlers return JSON error with keys:
  - error_code
  - message
"""
from typing import Optional

from flask import Response, jsonify
from structlog import get_logger
from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug.http import HTTP_STATUS_CODES

from .. import db
from . import bp

logger = get_logger(__name__)


def api_error_response(status_code: int, message: Optional[str] = None) -> Response:
    payload = {"error_code": HTTP_STATUS_CODES.get(status_code, "Unknown HTTP error")}
    if message is not None:
        payload["message"] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response


@bp.app_errorhandler(HTTPException)
def http_exception(exc: HTTPException) -> Response:
    logger.error("http_error", http_error_code=exc.code)
    return api_error_response(exc.code, str(exc))  # type: ignore


# TODO AppException handler


@bp.app_errorhandler(Exception)
def handle_exception(_: Exception) -> Response:
    db.session.rollback()
    logger.exception("unhandled_exception")
    return api_error_response(InternalServerError.code, InternalServerError.description)
