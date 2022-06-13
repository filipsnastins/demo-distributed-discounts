from typing import Optional

from flask_executor.executor import ExecutorJob
from structlog import get_logger

from .. import db
from ..models import AvailableDiscountCode, FetchedDiscountCode
from .exceptions import DiscountCodeAlreadyExistsError, DiscountCodeNotAvailableError

logger = get_logger()


def get_already_created_discount_code(
    campaign_id: int, user_id: int
) -> Optional[FetchedDiscountCode]:
    fetched_discount_code = FetchedDiscountCode.query.filter(
        FetchedDiscountCode.campaign_id == campaign_id,
        FetchedDiscountCode.user_id == user_id,
    ).first()
    if fetched_discount_code:
        return fetched_discount_code
    return None


def create_discount_code(
    campaign_id: int, user_id: int, code_fetched_event: Optional[ExecutorJob] = None
) -> FetchedDiscountCode:
    discount_code = get_already_created_discount_code(campaign_id, user_id)
    if discount_code:
        raise DiscountCodeAlreadyExistsError

    available_discount_code = (
        AvailableDiscountCode.query.with_for_update(skip_locked=True)
        .filter(AvailableDiscountCode.campaign_id == campaign_id)
        .first()
    )
    if not available_discount_code:
        raise DiscountCodeNotAvailableError

    fetched_discount_code = FetchedDiscountCode(
        id=available_discount_code.id,
        campaign_id=available_discount_code.campaign_id,
        user_id=user_id,
    )
    db.session.delete(available_discount_code)
    db.session.add(fetched_discount_code)
    db.session.commit()

    if code_fetched_event:
        code_fetched_event.submit(discount_code=fetched_discount_code)

    logger.info(
        "discount_code_created",
        id=fetched_discount_code.id,
        campaign_id=fetched_discount_code.campaign_id,
        user_id=fetched_discount_code.user_id,
    )
    return fetched_discount_code
