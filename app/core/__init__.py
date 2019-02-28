from flask import Blueprint

bp = Blueprint('core', __name__)

from . import models, routes  # noqa: F401, E402
