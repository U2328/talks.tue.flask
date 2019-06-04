from logging.config import dictConfig

from flask import Flask, request, g, Markup
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_babel import Babel, lazy_gettext as _l
from flask_moment import Moment
from flask_caching import Cache
from flask_mail import Mail
from flask_htmlmin import HTMLMIN

from celery import Celery
from markdown import Markdown


from .config import get_config


__all__ = ("create_app", "db", "migrate", "login", "babel", "moment", "celery", "md")

config = get_config()

csrf = CSRFProtect()
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
babel = Babel()
moment = Moment()
login.login_view = "auth.login"
login.login_message = _l("Please log in to access this page.")
cache = Cache(config={"CACHE_TYPE": "simple"})
mail = Mail()
htmlmin = HTMLMIN()
celery = Celery(__name__)
celery.config_from_object(config)
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


def markdown(text):
    return Markup(md.convert(text))


from app.core import bp as core_bp  # noqa: E402
from app.auth import bp as auth_bp  # noqa: E402
from app.api import bp as api_bp  # noqa: E402
from app.errors import bp as errors_bp  # noqa: E402


def create_app():
    config = get_config()
    app = Flask(__name__)
    app.config.from_object(config)

    csrf.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app)
    moment.init_app(app)
    login.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    htmlmin.init_app(app)
    app.jinja_env.filters.setdefault("markdown", markdown)

    from app import models, tasks, filters  # noqa: F402, F401

    _filters = {name: getattr(filters, name) for name in filters.__all__}
    app.jinja_env.filters.update(_filters)

    app.register_blueprint(core_bp)
    app.register_blueprint(errors_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @babel.localeselector
    def get_locale():
        return request.accept_languages.best_match(app.config["LANGUAGES"])

    def before_request():
        g.locale = str(get_locale())

    app.before_request(before_request)

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

    return app
