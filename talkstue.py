import os

import click
from flask_migrate import upgrade

from app import create_app, db, tasks
from app import models


app = create_app()


def get_all_in_all(module):
    return {
        model_name: getattr(module, model_name, None) for model_name in module.__all__
    }


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "tasks": tasks, **get_all_in_all(models)}


@app.cli.group()
def auth():
    """User  and authentication commands."""


@auth.command(with_appcontext=True)
@click.option(
    "--username", prompt=True, default=lambda: os.environ.get("ADMIN_USERNAME", "")
)
@click.option(
    "--email",
    prompt=True,
    default=lambda: os.environ.get("ADMIN_EMAIL", "test@example.com"),
)
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    default=lambda: "*" * len(os.environ.get("ADMIN_PASSWORD", "")),
)
def createsuperuser(username, email, password):
    """Create a superuser"""
    u = models.User(username=username, email=email, is_admin=True)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()


@app.cli.command()
def deploy():
    """Run deployment tasks."""
    upgrade()


if __name__ == "__main__":
    app.run()
