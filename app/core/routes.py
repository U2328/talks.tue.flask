from datetime import datetime

from flask import render_template, current_app

from app import db
from . import bp
from .models import Talk
from app.api.routes import TalkTable


@bp.route('/')
@bp.route('/index')
def index():
    talks = Talk.query[:9]
    return render_template('core/index.html', up_next=talks)

@bp.route('/talks')
def talks():
    table = TalkTable()
    return render_template('core/talks.html', title='Talks', table=table)
