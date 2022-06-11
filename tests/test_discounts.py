import datetime
import re

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from app import db
from app.discounts.code_generator import generate_discount_code
from app.models import AvailableDiscountCode, Campaign, FetchedDiscountCode, Marketplace

TEST_CAMPAIGN_ID = 100
TEST_USER_ID = 123456


def get_discount_code(
    client: FlaskClient, campaign_id: int = TEST_CAMPAIGN_ID, user_id: int = TEST_USER_ID
) -> TestResponse:
    return client.get(
        f"/discounts/{campaign_id}",
        headers={"Accept": "application/json", "Authorization": user_id},
    )


@pytest.fixture(name="create_test_discount_codes", autouse=True)
def create_test_discount_codes_fixture(app: Flask):
    with app.app_context():
        # Create Marketplace
        marketplace = Marketplace(
            name="My Test Shop",
            website_url="https://example.com",
            is_approved=True,
            is_active=True,
            discount_code_fetch_callback_method="webhook",
        )
        db.session.add(marketplace)
        db.session.commit()
        # Create Campaign
        campaign = Campaign(
            id=TEST_CAMPAIGN_ID,
            name="First Order 10% discount",
            active_until=datetime.datetime.utcnow() + datetime.timedelta(days=1),
            marketplace_id=marketplace.id,
        )
        db.session.add(campaign)
        db.session.commit()
        # Create available discount codes for the campaign
        for _ in range(100):
            discount_code = AvailableDiscountCode(
                id=generate_discount_code(), campaign_id=campaign.id
            )
            db.session.add(discount_code)
        db.session.commit()


def test_404_if_no_active_discount_codes_exist_for_the_campaign(
    app: Flask, client: FlaskClient
) -> None:
    with app.app_context():
        AvailableDiscountCode.query.delete()
        db.session.commit()

        res = get_discount_code(client)
        data = res.get_json()

        assert res.status_code == 404
        assert data["error_code"] == "AVAILABLE_DISCOUNT_CODE_NOT_FOUND"


def test_discount_code_created_for_user_first_time(app: Flask, client: FlaskClient) -> None:
    with app.app_context():
        res = get_discount_code(client)
        data = res.get_json()
        available_discount_code = AvailableDiscountCode.query.filter(
            AvailableDiscountCode.id == data["id"]
        ).first()
        fetched_discount_code = FetchedDiscountCode.query.filter(
            FetchedDiscountCode.id == data["id"],
            FetchedDiscountCode.campaign_id == TEST_CAMPAIGN_ID,
            FetchedDiscountCode.user_id == TEST_USER_ID,
        ).first()

        assert res.status_code == 201
        assert re.match("[A-Z 0-9]{9}", data["id"])
        assert data["is_used"] is False
        assert not available_discount_code
        assert fetched_discount_code


def test_discount_code_idempotently_returned_if_already_fetched(
    app: Flask, client: FlaskClient
) -> None:
    with app.app_context():
        fetch_first_res = get_discount_code(client)

        get_second_res = get_discount_code(client)
        data = get_second_res.get_json()
        fetched_discount_codes = FetchedDiscountCode.query.filter(
            FetchedDiscountCode.campaign_id == TEST_CAMPAIGN_ID,
            FetchedDiscountCode.user_id == TEST_USER_ID,
        ).all()

        assert fetch_first_res.status_code == 201
        assert get_second_res.status_code == 200
        assert len(fetched_discount_codes) == 1
        assert fetched_discount_codes[0].id == data["id"]
        assert data["is_used"] is False


def test_is_used_flag_set_to_true_if_code_has_been_marked_as_used(app: Flask, client: FlaskClient):
    with app.app_context():
        code_id = generate_discount_code()
        fetched_discount_code = FetchedDiscountCode(
            id=code_id, campaign_id=TEST_CAMPAIGN_ID, user_id=TEST_USER_ID, is_used=True
        )
        db.session.add(fetched_discount_code)
        db.session.commit()

        res = get_discount_code(client)
        data = res.get_json()

        assert res.status_code == 200
        assert data["id"] == code_id
        assert data["is_used"] is True
