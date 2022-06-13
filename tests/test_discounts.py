import datetime
import re
import time

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from app import db
from app.models import AvailableDiscountCode, Campaign, FetchedDiscountCode, Marketplace

TEST_CAMPAIGN_ID = "1"
TEST_USER_ID = "123456"


@pytest.fixture(name="create_test_discount_codes", autouse=True)
def create_test_discount_codes_fixture(app: Flask):
    with app.app_context():
        # Create Marketplace
        marketplace = Marketplace(
            name="My Test Shop",
            website_url="https://example.com",
            is_approved=True,
            is_active=True,
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
            discount_code = AvailableDiscountCode(campaign_id=campaign.id)
            db.session.add(discount_code)
        db.session.commit()


class TestCreateDiscountCode:
    def create_discount_code(
        self, client: FlaskClient, campaign_id: str = TEST_CAMPAIGN_ID, user_id: str = TEST_USER_ID
    ) -> TestResponse:
        return client.post(f"/api/discounts/{campaign_id}", headers={"Authorization": user_id})

    def test_401_if_authorization_token_is_not_sent(self, client: FlaskClient) -> None:
        res = self.create_discount_code(client, user_id="")
        data = res.get_json()

        assert res.status_code == 401
        assert data["error_code"] == "INVALID_ACCESS_TOKEN"

    def test_404_if_no_active_discount_codes_exist_for_the_campaign(
        self, app: Flask, client: FlaskClient
    ) -> None:
        with app.app_context():
            AvailableDiscountCode.query.delete()
            db.session.commit()

            res = self.create_discount_code(client)
            data = res.get_json()

            assert res.status_code == 404
            assert data["error_code"] == "DISCOUNT_CODE_NOT_AVAILABLE"

    def test_discount_code_created_for_user_first_time(
        self, app: Flask, client: FlaskClient
    ) -> None:
        with app.app_context():
            res = self.create_discount_code(client)
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

    def test_409_if_discount_code_has_been_already_created(
        self, app: Flask, client: FlaskClient
    ) -> None:
        with app.app_context():
            create_first = self.create_discount_code(client)

            create_second = self.create_discount_code(client)
            data = create_second.get_json()

            assert create_first.status_code == 201
            assert create_second.status_code == 409
            assert data["error_code"] == "DISCOUNT_CODE_ALREADY_FETCHED"


class TestGetDiscountCode:
    def get_discount_code(
        self, client: FlaskClient, campaign_id: str = TEST_CAMPAIGN_ID, user_id: str = TEST_USER_ID
    ) -> TestResponse:
        return client.get(f"/api/discounts/{campaign_id}", headers={"Authorization": user_id})

    def test_401_if_authorization_token_is_not_sent(self, client: FlaskClient) -> None:
        res = self.get_discount_code(client, user_id="")
        data = res.get_json()

        assert res.status_code == 401
        assert data["error_code"] == "INVALID_ACCESS_TOKEN"

    def test_404_if_discount_code_does_not_exist_for_given_user(self, client: FlaskClient):
        res = self.get_discount_code(client)
        data = res.get_json()

        assert res.status_code == 404
        assert data["error_code"] == "DISCOUNT_CODE_NOT_FOUND"

    def test_discount_code_found(self, app: Flask, client: FlaskClient):
        with app.app_context():
            code_id = "1234"
            fetched_discount_code = FetchedDiscountCode(
                id=code_id, campaign_id=TEST_CAMPAIGN_ID, user_id=TEST_USER_ID, is_used=True
            )
            db.session.add(fetched_discount_code)
            db.session.commit()

            res = self.get_discount_code(client)
            data = res.get_json()

            assert res.status_code == 200
            assert data["id"] == code_id
            assert data["is_used"] is True


class TestGenerateDiscountCodes:
    TEST_ADMIN_ID = "987654"
    GENERATE_COUNT = 2000

    def generate_discount_code_ids(
        self,
        client: FlaskClient,
        discount_codes_count: int = GENERATE_COUNT,
        campaign_id: str = TEST_CAMPAIGN_ID,
        admin_id: str = TEST_ADMIN_ID,
    ) -> TestResponse:
        return client.post(
            f"/api/discounts/{campaign_id}/manage/generate-codes",
            headers={"Content-Type": "application/json", "Authorization": admin_id},
            json={"discount_codes_count": discount_codes_count},
        )

    def test_401_if_authorization_token_is_not_sent(self, client: FlaskClient) -> None:
        res = self.generate_discount_code_ids(client, admin_id="")
        data = res.get_json()

        assert res.status_code == 401
        assert data["error_code"] == "INVALID_ACCESS_TOKEN"

    def test_404_if_campaign_does_not_exist(self, app: Flask, client: FlaskClient):
        with app.app_context():
            Campaign.query.delete()
            db.session.commit()

            res = self.generate_discount_code_ids(client)
            data = res.get_json()

            assert res.status_code == 404
            assert data["error_code"] == "CAMPAIGN_NOT_FOUND"

    def test_400_if_request_validation_failed(self, client: FlaskClient):
        res = self.generate_discount_code_ids(client, discount_codes_count="invalid number")
        data = res.get_json()

        assert res.status_code == 400
        assert data["error_code"] == "REQUEST_VALIDATION_FAILED"

    def test_discount_codes_generated_after_async_task_finishes(
        self, app: Flask, client: FlaskClient
    ):
        with app.app_context():
            AvailableDiscountCode.query.delete()
            db.session.commit()

            res = self.generate_discount_code_ids(client)
            data = res.get_json()
            # TODO Wait until background job is finished; dirty solution and flaky test
            time.sleep(3)
            discount_codes_count = AvailableDiscountCode.query.filter(
                AvailableDiscountCode.campaign_id == TEST_CAMPAIGN_ID
            ).count()

            assert res.status_code == 202
            assert data["job_id"]
            assert self.GENERATE_COUNT == discount_codes_count

    def test_discount_codes_are_generated_asynchronously(self, app: Flask, client: FlaskClient):
        with app.app_context():
            AvailableDiscountCode.query.delete()
            db.session.commit()

            self.generate_discount_code_ids(client)
            discount_codes_count = AvailableDiscountCode.query.filter(
                AvailableDiscountCode.campaign_id == TEST_CAMPAIGN_ID
            ).count()

            # Not all codes are generated yet without awaiting
            assert self.GENERATE_COUNT != 0
            assert self.GENERATE_COUNT > discount_codes_count
