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
    # Separate table for contacts
    website_url = db.Column(db.String(256), nullable=False)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    # Notification settings can be normalized in config table or moved to separate microservice
    discount_code_fetch_callback_method = db.Column(
        db.Enum("webhook", "amqp", name="marketplace_discount_code_fetch_callback_method"),
        nullable=True,
    )

    def __repr__(self):
        return f"<Marketplace> {self.name}"


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
        return f"<Campaign> {self.name}"


class AvailableDiscountCode(db.Model):
    __tablename__ = "available_discount_codes"

    id = db.Column(db.String(10), primary_key=True, nullable=False)
    campaign_id = db.Column(
        db.Integer, db.ForeignKey("campaigns.id"), primary_key=True, nullable=False
    )

    campaign = db.relationship("Campaign", backref="available_discount_codes", lazy=True)

    def __repr__(self):
        return f"<AvailableDiscountCode> {self.id} - {self.campaign_id}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
        }


class FetchedDiscountCode(db.Model):
    __tablename__ = "fetched_discount_codes"

    id = db.Column(
        db.String(10),
        db.ForeignKey("available_discount_codes.id"),
        primary_key=True,
        nullable=False,
    )
    campaign_id = db.Column(
        db.Integer, db.ForeignKey("campaigns.id"), primary_key=True, nullable=False
    )
    # Getting user_id from authentication microservice
    user_id = db.Column(db.Integer, primary_key=True, index=True, nullable=False)
    is_used = db.Column(db.Boolean, nullable=False, default=False)

    campaign = db.relationship("Campaign", backref="fetched_discount_codes", lazy=True)

    def __repr__(self) -> str:
        return f"<FetchedDiscountCode> {self.id} - {self.campaign_id} - {self.user_id}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "user_id": self.user_id,
            "is_used": self.is_used,
        }
