from flask import render_template

from . import bp
from .models import Talk
from app.api.routes import TalkTable


__all__ = (
    'index',
    'talks'
)


@bp.route('/')
@bp.route('/index')
def index():
    talks = Talk.query[:9]
    return render_template('core/index.html', up_next=talks)


@bp.route('/talks')
def talks():
    table = TalkTable()
    return render_template('core/talks.html', title='Talks', table=table)
