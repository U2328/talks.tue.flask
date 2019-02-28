from flask import Blueprint

bp = Blueprint('auth', __name__)

from . import models, routes  # noqa: F401, E402
