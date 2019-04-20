from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from flask_caching import Cache
from flask import Markup
from markdown import Markdown
from logging.config import dictConfig

from app.config import Config


__all__ = (
    'db', 'migrate', 'login',
    'md', 'create_app', 'babel',
    'moment',
)

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
babel = Babel()
moment = Moment()
login.login_view = 'auth.login'
login.login_message = _l('Please log in to access this page.')
cache = Cache(config={
    "CACHE_TYPE": "simple"
})
md = Markdown(
    extensions=[
        "markdown.extensions.sane_lists",
        "markdown.extensions.nl2br",
        "markdown.extensions.codehilite",
        "pymdownx.extra",
        "pymdownx.arithmatex",
        "pymdownx.smartsymbols",
    ],
    extension_configs={
        "pymdownx.arithmatex": {
            "generic": True,
        }
    },
)


def markdown(text):
    return Markup(md.convert(text))


from app.core import bp as core_bp  # noqa: E402
from app.auth import bp as auth_bp  # noqa: E402
from app.api import bp as api_bp  # noqa: E402
from app.errors import bp as errors_bp  # noqa: E402
from app.admin import bp as admin_bp  # noqa: E402


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    babel.init_app(app)
    moment.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    cache.init_app(app)
    app.jinja_env.filters.setdefault('markdown', markdown)

    from app import models as _  # noqa: E402, F401

    app.register_blueprint(core_bp)
    app.register_blueprint(errors_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')


    @babel.localeselector
    def get_locale():
        return request.accept_languages.best_match(app.config['LANGUAGES'])

    def before_request():
        g.locale = str(get_locale())

    app.before_request(before_request)

    dictConfig({
        'version': 1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s %(levelname)8s] %(message)s | %(name)s:%(lineno)d'
            }
        },
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default'
            },
        },
        'loggers': {
            'flask.app': {
                'handlers': ['wsgi'],
                'level': 'DEBUG' if app.debug else 'INFO'
            },
        }
    })

    return app
