import os


__all__ = ("get_config", "ProductionConfig", "DevelopmentConfig", "TestingConfig")

basedir = os.path.abspath(os.path.dirname(__file__))


def get_config():
    return f"app.config.{os.environ.get('CONFIG', 'Production')}Config"


class Config:
    # Base
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY") or "ultra-secret-key"
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or "sqlite:///" + os.path.join(
        basedir, "app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Babel
    LANGUAGES = list(os.getenv("LANGUAGES", "en,de").split(","))
    # Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BORKER_URL")


class ProductionConfig(Config):
    ...


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
