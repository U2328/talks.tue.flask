from flask import render_template, current_app, abort, request
from flask_login import current_user

from . import bp
from app.models import Talk, Collection
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


@bp.route('/talk')
@bp.route('/talk/<int:id>')
def talk(id=None):
    id = id or request.args.get("id")
    if id is None:
        return abort(404)
    talk = Talk.query.get(id)
    if talk is None:
        return abort(404)
    return render_template('core/talk.html', title=talk.title, talk=talk, can_edit=talk.can_edit(current_user))


@bp.route('/collection')
@bp.route('/collection/<int:id>')
def collection(id=None):
    id = id or request.args.get("id")
    if id is None:
        return abort(404)
    collection = Collection.query.get(id)
    if collection is None:
        return abort(404)
    return render_template('core/collection.html', title=collection.title, collection=collection, can_edit=collection.can_edit(current_user))
