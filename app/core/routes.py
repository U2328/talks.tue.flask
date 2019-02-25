from datetime import datetime

from flask import render_template

from app import db
from . import bp
from .models import Talk


@bp.route('/')
@bp.route('/index')
def index():
    talks = Talk.query[:9]
    return render_template('core/index.html', up_next=talks)

@bp.route('/talks')
def talks():
    return render_template('core/talks.html', title='Talks')
