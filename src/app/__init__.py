from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from structlog import get_logger

from .config import get_settings
from .util.structlog import configure_structlog_logging

__version__ = "0.1.0"

logger = get_logger(__name__)

db = SQLAlchemy()


def create_app() -> Flask:
    # Configure Flask application object
    app = Flask(__name__)

    app_config = get_settings()
    app.config.from_object(app_config)

    configure_structlog_logging(production=bool(app_config.ENV == "production"))

    # Init Flask plugins
    db.init_app(app)

    # Add routes
    # fmt: off
    from .errors.handlers import bp as errors_bp  # noqa
    app.register_blueprint(errors_bp)

    from .discounts import bp as discounts_bp  # noqa
    app.register_blueprint(discounts_bp, url_prefix="/discounts")
    # fmt: on

    return app


from . import models  # noqa
