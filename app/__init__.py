from logging.config import dictConfig

from flask import Flask, request, g, Markup
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_babel import Babel, lazy_gettext as _l
from flask_caching import Cache
from flask_mail import Mail
from flask_htmlmin import HTMLMIN
from kombu.serialization import register
from celery import Celery

from markdown import Markdown

from .serialization import Binary
from .config import get_config


__all__ = ("create_app", "db", "migrate", "login", "babel", "celery", "md")


CONFIG = get_config()


# build flask app
app = Flask(__name__)
app.config.from_object(CONFIG)

# setup flask extensions
csrf = CSRFProtect(app=app)
db = SQLAlchemy(app=app)
migrate = Migrate(app=app, db=db)
babel = Babel(app=app)
login = LoginManager(app=app)
login.login_view = "auth.login"
login.login_message = _l("Please log in to access this page.")
cache = Cache(app=app, config={"CACHE_TYPE": "simple"})
mail = Mail(app=app)
htmlmin = HTMLMIN(app=app)
md = Markdown(
    extensions=[
        "markdown.extensions.sane_lists",
        "markdown.extensions.nl2br",
        "markdown.extensions.codehilite",
        "pymdownx.extra",
        "pymdownx.arithmatex",
        "pymdownx.smartsymbols",
    ],
    extension_configs={"pymdownx.arithmatex": {"generic": True}},
)
app.jinja_env.filters.setdefault("markdown", lambda text: Markup(md.convert(text)))

# link custom serializers
register(
    "bin",
    Binary.serialize,
    Binary.deserialize,
    content_type="application/bin",
    content_encoding="bin",
)
"""
register(
    "json",
    Json.serialize,
    Json.deserialize,
    content_type="application/json",
    content_encoding="utf-8",
)
"""

# setup celery
celery = Celery(__name__, broker=CONFIG.CELERY_BROKER_URL)
celery.config_from_object(CONFIG)

TaskBase = celery.Task


class ContextTask(TaskBase):  # type: ignore
    abstract = True

    def __call__(self, *args, **kwargs):
        with app.app_context(), app.test_request_context("/"):
            return super().__call__(*args, **kwargs)


celery.Task = ContextTask

# load non-blueprint modules
from app import models, tasks, filters  # noqa: F402, F401

# register filters from filter.__all__
_filters = {name: getattr(filters, name) for name in filters.__all__}
app.jinja_env.filters.update(_filters)

# register blueprints
from app.core import bp as core_bp  # noqa: E402
from app.auth import bp as auth_bp  # noqa: E402
from app.api import bp as api_bp  # noqa: E402
from app.errors import bp as errors_bp  # noqa: E402

app.register_blueprint(core_bp)
app.register_blueprint(errors_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp, url_prefix="/api")

# integrate locale injection
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config["LANGUAGES"])


def before_request():
    g.locale = str(get_locale())
    g.server_name = app.config["SERVER_NAME"]


app.before_request(before_request)

# setup logging
dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s %(levelname)8s] %(message)s | %(name)s:%(lineno)d"
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "loggers": {
            "flask.app": {
                "handlers": ["wsgi"],
                "level": "DEBUG" if app.debug else "INFO",
            }
        },
    }
)
