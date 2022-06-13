from structlog import get_logger

from .. import db, executor
from ..models import FetchedDiscountCode

logger = get_logger(__name__)


@executor.job
def send_discount_code_fetched_event(discount_code: FetchedDiscountCode):
    # Placing event to a queue asynchronously
    logger.info(
        "send_discount_code_fetched_event",
        discount_code_id=discount_code.id,
        campaign_id=discount_code.campaign_id,
        user_id=discount_code.user_id,
    )
    discount_code.is_fetched_event_sent = True
    db.session.add(discount_code)
    db.session.commit()
