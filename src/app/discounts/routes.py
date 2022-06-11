from flask import jsonify
from structlog import get_logger

from app.errors.exceptions import AppError

from .. import db
from ..models import AvailableDiscountCode, FetchedDiscountCode
from . import bp

logger = get_logger()


@bp.get("/<campaign_id>")
def get_discount_code(campaign_id: int):
    # If code is already created for the user, return it
    fetched_discount_code = FetchedDiscountCode.query.filter(
        FetchedDiscountCode.campaign_id == campaign_id,
        # TODO take user id from request headers/simulate getting user id from jwt token
        FetchedDiscountCode.user_id == "123456",
    ).first()
    if fetched_discount_code:
        return jsonify(fetched_discount_code.to_dict()), 200

    # Get available discount code if any
    available_discount_code = AvailableDiscountCode.query.filter(
        AvailableDiscountCode.campaign_id == campaign_id
    ).first()
    if not available_discount_code:
        raise AppError(error_code="AVAILABLE_DISCOUNT_CODE_NOT_FOUND", status_code=404)

    # Move fetched discount code to another table
    fetched_discount_code = FetchedDiscountCode(
        id=available_discount_code.id,
        campaign_id=available_discount_code.campaign_id,
        # TODO take user id from request headers/simulate getting user id from jwt token
        user_id="123456",
    )
    db.session.delete(available_discount_code)
    db.session.add(fetched_discount_code)
    db.session.commit()
    return jsonify(fetched_discount_code.to_dict()), 201
