from . import celery, create_app
from app.tasks import *  # noqa: F401, F403


app = create_app()

TaskBase = celery.Task


class ContextTask(TaskBase):  # type: ignore
    abstract = True

    def __call__(self, *args, **kwargs):
        with app.app_context():
            return TaskBase.__call__(self, *args, **kwargs)


celery.Task = ContextTask
