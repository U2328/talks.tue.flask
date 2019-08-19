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
    VERSION = "0.2.6"
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "ultra-secret-key")
    DATE_FORMAT = "%d.%m.%Y"
    TIME_FORMAT = "%H:%M"
    SERVER_NAME = os.getenv("SERVER_NAME", "localhost")

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgres://postgres:@db:5432/talks_tue"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Babel
    LANGUAGES = list(os.getenv("LANGUAGES", "en,de").split(","))

    # Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://talks_tue@rabbit:5672//")
    CELERY_RESULT_BACKEND = os.getenv(
        "CELERY_BACKEND_URL", "rpc://talks_tue@rabbit:5672//"
    )
    CELERY_ACCEPT_CONTENT = ["bin"]
    CELERY_TASK_SERIALIZER = "bin"
    CELERY_RESULT_SERIALIZER = "bin"
    CELERY_IMPORTS = ("app.tasks",)
    CELERYBEAT_SCHEDULE = {
        "daily-reminder": {
            "task": "app.tasks.send_subscription_emails",
            "args": ("daily",),
            "schedule": crontab(hour="4", minute="0"),
        },
        "weekly-reminder": {
            "task": "app.tasks.send_subscription_emails",
            "args": ("weekly",),
            "schedule": crontab(day_of_week="0", hour="4", minute="0"),
        },
    }

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 25))  # 25 is traditional SMTP port
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_USE_TLS = bool(os.getenv("MAIL_USE_TLS", False))
    MAIL_USE_SSL = bool(os.getenv("MAIL_USE_SSL", False))
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "test@example.com")


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
