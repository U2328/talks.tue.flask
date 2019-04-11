from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_pagedown import PageDown
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l, get_locale
from flaskext.markdown import Markdown
import sqlalchemy
from sqlalchemy_continuum import make_versioned
from sqlalchemy_continuum.plugins import ActivityPlugin, FlaskPlugin

from app.config import Config


__all__ = (
    'db', 'migrate', 'login',
    'md', 'create_app', 'babel',
    'moment', 'pagedown'
)

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
babel = Babel()
moment = Moment()
login.login_view = 'auth.login'
login.login_message = _l('Please log in to access this page.')
pagedown = PageDown()

db_activity = ActivityPlugin()
make_versioned(plugins=[db_activity, FlaskPlugin()])

from app.core import bp as core_bp  # noqa: E402
from app.auth import bp as auth_bp  # noqa: E402
from app.api import bp as api_bp  # noqa: E402
from app.errors import bp as errors_bp  # noqa: E402
from app.admin import bp as admin_bp  # noqa: E402


def before_request():
    g.locale = str(get_locale())


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    babel.init_app(app)
    moment.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    pagedown.init_app(app)
    markdown = Markdown(  # noqa: F841
        app,
        extenensions=[
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
        }
    )

    from app import models as _  # noqa: E402, F401

    sqlalchemy.orm.configure_mappers()

    app.register_blueprint(core_bp)
    app.register_blueprint(errors_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    @babel.localeselector
    def get_locale():
        return request.accept_languages.best_match(app.config['LANGUAGES'])

    app.before_request(before_request)

    return app
