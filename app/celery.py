from . import celery, create_app  # noqa: F401

if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
