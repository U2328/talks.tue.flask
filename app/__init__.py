from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_pagedown import PageDown
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l, get_locale
from flaskext.markdown import Markdown

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


from app.core import bp as core_bp  # noqa: E402
from app.auth import bp as auth_bp, models as auth_models  # noqa: E402
from app.api import bp as api_bp  # noqa: E402
from app.errors import bp as errors_bp  # noqa: E402
from app.admin import bp as admin_bp  # noqa: E402


def context_processor():
    return {
        'can_view_admin': hasattr(current_user, 'role') and current_user.role.name != auth_models.Role.DEFAULT_ROLE,
    }


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
    markdown = Markdown(app)  # noqa: F841

    app.register_blueprint(core_bp)
    app.register_blueprint(errors_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    @babel.localeselector
    def get_locale():
        return request.accept_languages.best_match(app.config['LANGUAGES'])

    app.context_processor(context_processor)
    app.before_request(before_request)

    return app
