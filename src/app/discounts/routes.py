from flask import jsonify, request
from structlog import get_logger

from ..auth import current_user
from ..config import get_settings
from ..errors.exceptions import AppError
from . import bp
from .code_fetch import create_discount_code, get_already_created_discount_code
from .code_generation import start_generate_discount_codes_job
from .events import send_discount_code_fetched_event
from .exceptions import (
    CampaignNotFoundError,
    DiscountCodeAlreadyExistsError,
    DiscountCodeNotAvailableError,
)

logger = get_logger(__name__)


@bp.post("/<campaign_id>")
def create_discount_code_route(campaign_id: int):
    """Create new discount code for given campaign and given user.

    Response status code:
        - 201 - discount code created.
    Response body:
        - id (str)
        - campaign_id (int)
        - user_id (int)
        - is_used (bool)

    Error codes:
        - INVALID_ACCESS_TOKEN (HTTP 401)
        - DISCOUNT_CODE_NOT_AVAILABLE (HTTP 404)
        - DISCOUNT_CODE_ALREADY_FETCHED (HTTP 409)
    """
    user = current_user()
    try:
        discount_code = create_discount_code(
            campaign_id=campaign_id,
            user_id=user["id"],
            code_fetched_event=send_discount_code_fetched_event,
        )
    except DiscountCodeNotAvailableError as exc:
        raise AppError(error_code="DISCOUNT_CODE_NOT_AVAILABLE", status_code=404) from exc
    except DiscountCodeAlreadyExistsError as exc:
        raise AppError(error_code="DISCOUNT_CODE_ALREADY_FETCHED", status_code=409) from exc
    return jsonify(discount_code.to_dict()), 201


@bp.get("/<campaign_id>")
def get_discount_code_route(campaign_id: int):
    """Get already created discount code for given campaign and given user.

    Response status code:
        - 200
    Response body:
        - id (str)
        - campaign_id (int)
        - user_id (int)
        - is_used (bool)

    Error codes:
        - INVALID_ACCESS_TOKEN (HTTP 401)
        - DISCOUNT_CODE_NOT_FOUND (HTTP 404)
    """
    user = current_user()
    discount_code = get_already_created_discount_code(campaign_id=campaign_id, user_id=user["id"])
    if not discount_code:
        raise AppError(error_code="DISCOUNT_CODE_NOT_FOUND", status_code=404)
    return jsonify(discount_code.to_dict())


@bp.post("/<campaign_id>/manage/generate-codes")
def generate_discount_codes_route(campaign_id: int):
    """Create new discount code generation job for a given campaign.
    The job will be processed in the background.

    Request body:
        - discount_codes_count (int) - count of codes to be generated.

    Response status code:
        - 202 - job has been created.
    Response body:
        - job_id (str) - created job id.

    Error codes:
        - INVALID_ACCESS_TOKEN (HTTP 401)
        - REQUEST_VALIDATION_FAILED (HTTP 400)
        - CAMPAIGN_NOT_FOUND (HTTP 404)
    """
    current_user()
    data = request.get_json()
    try:
        discount_codes_count = int(data["discount_codes_count"])
        if not discount_codes_count or discount_codes_count < 0:
            raise ValueError
    except (KeyError, ValueError) as exc:
        raise AppError(
            error_code="REQUEST_VALIDATION_FAILED",
            error_message="'discount_codes_count' must be a positive integer",
            status_code=400,
        ) from exc

    try:
        app_config = get_settings()
        job_id = start_generate_discount_codes_job(
            campaign_id=campaign_id,
            discount_codes_count=discount_codes_count,
            commit_batch=app_config.DISCOUNT_CODE_GENERATION_COMMIT_BATCH,
        )
    except CampaignNotFoundError as exc:
        raise AppError(error_code="CAMPAIGN_NOT_FOUND", status_code=404) from exc
    return jsonify({"job_id": job_id}), 202
