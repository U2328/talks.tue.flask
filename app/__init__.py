from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_pagedown import PageDown
from flaskext.markdown import Markdown

from app.config import Config


__all__ = (
    'db', 'migrate', 'login',
    'md', 'create_app'
)


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
# login.login_message = _l('Please log in to access this page.')
pagedown = PageDown()

from app.core import bp as core_bp
from app.auth import bp as auth_bp
from app.api import bp as api_bp
from app.errors import bp as errors_bp
from app.admin import bp as admin_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    pagedown.init_app(app)
    markdown = Markdown(app)
    
    app.register_blueprint(core_bp)
    app.register_blueprint(errors_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
