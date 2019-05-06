from . import celery, create_app  # noqa: F401
from app.tasks import *  # noqa: F401, F403


app = create_app()
app.app_context().push()
