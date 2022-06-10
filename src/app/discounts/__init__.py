from flask import Blueprint

bp = Blueprint("discounts", __name__)

from . import routes  # noqa
