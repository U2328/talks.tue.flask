from flask import render_template, current_app
from flask_login import current_user

from . import bp
from app.models import Talk
from app.api.routes import TalkTable


__all__ = (
    'index',
    'talks'
)


@bp.route('/')
@bp.route('/index')
def index():
    current_app.logger.info(current_user)
    talks = Talk.query[:9]
    return render_template('core/index.html', up_next=talks)


@bp.route('/talks')
def talks():
    table = TalkTable()
    return render_template('core/talks.html', title='Talks', table=table)
