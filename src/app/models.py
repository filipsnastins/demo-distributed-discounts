from __future__ import annotations

import uuid

from . import db


class Marketplace(db.Model):
    __tablename__ = "marketplace"

    id = db.Column(
        db.Integer,
        db.Sequence("marketplace_id_seq", start=1, increment=1),
        primary_key=True,
        nullable=False,
    )
    name = db.Column(db.String(256), nullable=False, unique=True, index=True)
    website_url = db.Column(db.String(256), nullable=False)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<Marketplace> {self.id} - {self.name}"


class Campaign(db.Model):
    __tablename__ = "campaigns"

    id = db.Column(
        db.Integer,
        db.Sequence("campaign_id_seq", start=1, increment=1),
        primary_key=True,
        nullable=False,
    )
    name = db.Column(db.String(256), nullable=False)
    active_until = db.Column(db.DateTime, nullable=True)
    marketplace_id = db.Column(db.Integer, db.ForeignKey("marketplace.id"), nullable=False)
    marketplace = db.relationship("Marketplace", backref="campaigns", lazy=True)

    def __repr__(self) -> str:
        return f"<Campaign> {self.id} - {self.name}"


class AvailableDiscountCode(db.Model):
    __tablename__ = "available_discount_codes"

    id = db.Column(
        db.String(10),
        primary_key=True,
        # pylint: disable=unnecessary-lambda
        default=lambda: AvailableDiscountCode.generate_new_code_id(),
        unique=True,
        nullable=False,
    )
    campaign_id = db.Column(
        db.Integer, db.ForeignKey("campaigns.id"), primary_key=True, nullable=False
    )
    campaign = db.relationship("Campaign", backref="available_discount_codes", lazy=True)

    def __repr__(self):
        return f"<AvailableDiscountCode> {self.id} - {self.campaign_id}"

    @staticmethod
    def generate_new_code_id() -> str:
        """Returns new 10 char discount code good enough for demo purposes."""
        id_1 = str(uuid.uuid4()).upper()
        id_2 = str(uuid.uuid4()).upper()
        return id_1[:8] + id_2[:2]

    # In the real-world app, schema returned to the client would be separated from DB model
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
        }


class FetchedDiscountCode(db.Model):
    __tablename__ = "fetched_discount_codes"

    id = db.Column(
        db.String(10),
        primary_key=True,
        unique=True,
        nullable=False,
    )
    campaign_id = db.Column(
        db.Integer, db.ForeignKey("campaigns.id"), primary_key=True, nullable=False
    )
    # Getting user_id from authentication microservice
    user_id = db.Column(db.Integer, primary_key=True, nullable=False)
    is_used = db.Column(db.Boolean, nullable=False, default=False)
    is_fetched_event_sent = db.Column(db.Boolean, nullable=False, default=False)
    campaign = db.relationship("Campaign", backref="fetched_discount_codes", lazy=True)

    def __repr__(self) -> str:
        return f"<FetchedDiscountCode> {self.id} - {self.campaign_id} - {self.user_id}"

    # In the real-world app, schema returned to the client would be separated from DB model
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "user_id": self.user_id,
            "is_used": self.is_used,
        }
