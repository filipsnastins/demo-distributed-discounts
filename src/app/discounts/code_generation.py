import time
import uuid

from structlog import get_logger

from .. import db, executor
from ..models import AvailableDiscountCode, Campaign
from .exceptions import CampaignNotFoundError

logger = get_logger(__name__)


def start_generate_discount_codes_job(
    campaign_id: int, discount_codes_count: int, commit_batch: int = 100000
):
    campaign = Campaign.query.filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise CampaignNotFoundError
    job_id = str(uuid.uuid4())
    __generate_discount_codes_job.submit(
        job_id=job_id,
        campaign=campaign,
        discount_codes_count=discount_codes_count,
        commit_batch=commit_batch,
    )
    return job_id


@executor.job
def __generate_discount_codes_job(
    job_id: str, campaign: Campaign, discount_codes_count: int, commit_batch
):
    start_time = time.time()
    log = logger.bind(job_id=job_id, campaign=campaign, discount_codes_count=discount_codes_count)
    log.info("generate_discount_codes_job", started=True)

    flush_counter = 0
    for _ in range(discount_codes_count):
        discount_code = AvailableDiscountCode(campaign_id=campaign.id)
        db.session.add(discount_code)
        flush_counter += 1
        if flush_counter > commit_batch:
            flush_counter = 0
            db.session.commit()
            db.session.flush()
    db.session.commit()
    db.session.flush()

    finished_in_seconds = time.time() - start_time
    log.info(
        "generate_discount_codes_job",
        finished=True,
        finished_in_seconds=finished_in_seconds,
    )
