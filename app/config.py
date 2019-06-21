import os

from celery.schedules import crontab

__all__ = ("get_config", "ProductionConfig", "DevelopmentConfig", "TestingConfig")

basedir = os.path.abspath(os.path.dirname(__file__))


_config_registry = {}


def _register_config(cls):
    _config_registry[cls.__name__] = cls
    return cls


def get_config():
    default = "Development" if os.getenv("FLASK_DEBUG", None) else "Production"
    return _config_registry[f"{os.environ.get('CONFIG', default)}Config"]


class Config:
    # Base
    VERSION = "0.2.4"
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY") or "ultra-secret-key"
    DATETIME_FORMAT = "%d.%m.%Y %H:%M"

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgres://postgres:@db:5432/talks_tue"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Babel
    LANGUAGES = list(os.getenv("LANGUAGES", "en,de").split(","))

    # Celery
    BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://talks_tue@rabbit:5672//")
    CELERY_RESULT_BACKEND = os.getenv(
        "CELERY_BACKEND_URL", "rpc://talks_tue@rabbit:5672//"
    )
    CELERY_IMPORTS = ("app.tasks",)
    CELERYBEAT_SCHEDULE = dict()


@_register_config
class ProductionConfig(Config):
    MINIFY_PAGE = True


@_register_config
class DevelopmentConfig(Config):
    DEBUG = True


@_register_config
class TestingConfig(Config):
    TESTING = True

    # Mail
    MAIL_SUPPRESS_SEND = True
