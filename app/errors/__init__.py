from flask import Blueprint

bp = Blueprint('errors', __name__)

from . import routes  # noqa: F401, E402
