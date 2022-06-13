import datetime

from flask import Flask
from structlog import get_logger

from app import create_app, db
from app.models import AvailableDiscountCode, Campaign, Marketplace

logger = get_logger(__name__)

TEST_CAMPAIGN_ID_1 = "1"
TEST_CAMPAIGN_ID_2 = "2"
DISCOUNT_CODE_COUNT = 10000


def initial_data(app: Flask):
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Create Marketplace
        marketplace_1 = Marketplace(
            name="My Test Shop 1",
            website_url="https://shop1.com",
            is_approved=True,
            is_active=True,
        )
        marketplace_2 = Marketplace(
            name="My Test Shop 2",
            website_url="https://shop2.com",
            is_approved=True,
            is_active=True,
        )
        db.session.add(marketplace_1)
        # db.session.add(marketplace_2)
        db.session.commit()

        # Create Campaign
        campaign_1 = Campaign(
            id=TEST_CAMPAIGN_ID_1,
            name="First Order 10% discount",
            active_until=datetime.datetime.utcnow() + datetime.timedelta(days=1),
            marketplace_id=marketplace_1.id,
        )
        campaign_2 = Campaign(
            id=TEST_CAMPAIGN_ID_2,
            name="Summer Sale",
            active_until=datetime.datetime.utcnow() + datetime.timedelta(days=1),
            marketplace_id=marketplace_2.id,
        )

        db.session.add(campaign_1)
        # db.session.add(campaign_2)
        db.session.commit()

        # Create available discount codes for the campaign
        for _ in range(DISCOUNT_CODE_COUNT):
            discount_code_1 = AvailableDiscountCode(campaign_id=campaign_1.id)
            # discount_code_2 = AvailableDiscountCode(campaign_id=campaign_2.id)
            db.session.add(discount_code_1)
            # db.session.add(discount_code_2)
        db.session.commit()


if __name__ == "__main__":
    app = create_app()
    logger.info("creating_initial_data")
    initial_data(app)
    logger.info("initial_data_created")
