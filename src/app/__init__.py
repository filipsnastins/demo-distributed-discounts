from flask import Flask
from flask_executor import Executor
from flask_sqlalchemy import SQLAlchemy
from structlog import get_logger

from .config import get_settings
from .middleware import enrich_structlog_with_request_context
from .util.structlog import configure_structlog_logging

__version__ = "0.1.0"

logger = get_logger(__name__)

db = SQLAlchemy()
executor = Executor()


def create_app() -> Flask:
    # Configure Flask application object
    app = Flask(__name__)

    app_config = get_settings()
    app.config.from_object(app_config)

    configure_structlog_logging(is_production=app_config.is_production)

    # Init Flask plugins
    db.init_app(app)
    executor.init_app(app)

    # Add routes
    # fmt: off
    app.before_request(enrich_structlog_with_request_context)

    from .errors.handlers import bp as errors_bp  # noqa
    app.register_blueprint(errors_bp)

    from .discounts import bp as discounts_bp  # noqa
    app.register_blueprint(discounts_bp, url_prefix="/api/discounts")
    # fmt: on

    return app


from . import models  # noqa
