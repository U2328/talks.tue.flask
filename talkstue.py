import os

import click
from flask.cli import AppGroup, with_appcontext
from flask_migrate import upgrade

from app import create_app, cli, db
from app.core import models as core_models
from app.auth import models as auth_models

app = create_app()
cli.register(app)


def get_all_in_all(module):
    return {
        model_name: getattr(module, model_name, None)
        for model_name in module.__all__
    }


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        **get_all_in_all(core_models),
        **get_all_in_all(auth_models),
    }


@app.cli.group()
def auth():
    """User  and authentication commands."""


@auth.command(with_appcontext=True)
@click.option('--username', prompt=True,
              default=lambda: os.environ.get('ADMIN_USERNAME', ''))
@click.option('--email', prompt=True,
              default=lambda: os.environ.get('ADMIN_EMAIL', 'test@example.com'))
@click.option('--password', prompt=True, hide_input=True,
              default=lambda: '*' * len(os.environ.get('ADMIN_PASSWORD', '')),)
def createsuperuser(username, email, password):
    """Create a superuser"""
    u = auth_models.User(username=username, email=email)
    u.set_password(password)
    u.role = auth_models.Role.query.filter_by(name='admin').first()
    db.session.add(u)
    db.session.commit()


@app.cli.group()
def translate():
    """Translation and localization commands."""
    ...


@translate.command()
def update():
    """Update all languages."""
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('extract command failed')
    if os.system('pybabel update -i messages.pot -d app/translations'):
        raise RuntimeError('update command failed')
    os.remove('messages.pot')


@translate.command()
def compile():
    """Compile all languages."""
    if os.system('pybabel compile -d app/translations'):
        raise RuntimeError('compile command failed')


@translate.command()
@click.option('--lang', prompt=True)
def init(lang):
    """Initialize a new language."""
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('extract command failed')
    if os.system(
            'pybabel init -i messages.pot -d app/translations -l ' + lang):
        raise RuntimeError('init command failed')
    os.remove('messages.pot')


@app.cli.command()
def deploy():
    """Run deployment tasks."""
    upgrade()
    auth_models.Role.insert_roles()


if __name__ == '__main__':
    app.run()
