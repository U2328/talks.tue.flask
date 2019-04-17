from flask import render_template, request, redirect,\
                  url_for, abort, current_app
from flask_login import current_user
from sqlalchemy import and_

from . import bp
from .forms import TalkForm, TagForm, CollectionForm
from app import db
from app.utils import is_safe_url, copy_row
from app.api.routes import TalkTable, CollectionTable, HistoryItemTable
from app.models import Talk, Tag, Collection, HistoryItem, HISTORY_DISCRIMINATOR_MAP


__all__ = (
    'tag',
    'talk',
)


@bp.route('/tag', methods=['POST'])
def tag():
    if not current_user.is_admin:
        return abort(403)
    form = TagForm(request.form)
    if form.validate_on_submit():
        tag = Tag()
        form.populate_obj(tag)
        db.session.add(tag)
        db.session.commit()
    next = request.args.get('next')
    if not is_safe_url(next):
        return abort(400)
    return redirect(next or url_for('core.index'))


@bp.route('/talk', methods=['GET', 'POST'])
@bp.route('/talk/<int:id>', methods=['GET', 'POST'])
def talk(id=None):
    talk = Talk() if id is None else Talk.query.get(id)

    if talk is None and id is not None:
        return abort(404)
    if id is not None and not talk.can_edit(current_user):
        return abort(403)
    if request.args.get('copy', False):
        talk = copy_row(talk, ['id'])

    next = request.args.get('next')
    if not is_safe_url(next):
        return abort(400)
    else:
        next = next or url_for('admin.talks')

    is_new = talk.id is None
    form = TalkForm(obj=talk)

    if form.validate_on_submit():
        form.populate_obj(talk)
        if is_new:
            db.session.add(talk)
        HistoryItem.build_for(talk)
        db.session.commit()
        return redirect(next)

    return render_template('admin/talk.html', title="Talk - Admin", form=form, new=is_new, next=next, talk=talk)


@bp.route('/talk/<int:id>/delete', methods=['GET', 'POST'])
def delete_talk(id):
    talk = Talk.query.get(id)

    if talk is None:
        return abort(404)
    if not talk.can_edit(current_user):
        return abort(403)

    next = request.args.get('next')
    if not is_safe_url(next):
        return abort(400)
    else:
        next = next or url_for('admin.talks')

    db.session.delete(talk)
    HistoryItem.build_for(talk)
    db.session.commit()
    return redirect(next)


@bp.route('/talks', methods=['GET'])
def talks():
    return render_template(
        'admin/talks.html',
        title="Talks - Admin",
        talk_table=TalkTable()
    )


@bp.route('/collection', methods=['GET', 'POST'])
@bp.route('/collection/<int:id>', methods=['GET', 'POST'])
def collection(id=None):
    collection = Collection() if id is None else Collection.query.get(id)

    if collection is None and id is not None:
        return abort(404)
    if id is not None and not collection.can_edit(current_user):
        return abort(403)
    if request.args.get('copy', False):
        collection = copy_row(collection, ['id'])

    next = request.args.get('next')
    if not is_safe_url(next):
        return abort(400)
    else:
        next = next or url_for('admin.collections')

    is_new = collection.id is None
    form = CollectionForm(obj=collection)

    if form.validate_on_submit():
        form.populate_obj(collection)
        if is_new:
            db.session.add(collection)
        HistoryItem.build_for(collection)
        db.session.commit()
        return redirect(next)

    return render_template('admin/collection.html', title="Collection - Admin", form=form, new=is_new, next=next, collection=collection)


@bp.route('/collection/<int:id>/delete', methods=['GET', 'POST'])
def delete_collection(id):
    collection = Collection.query.get(id)

    if collection is None:
        return abort(404)
    if not collection.can_edit(current_user):
        return abort(403)

    next = request.args.get('next')
    if not is_safe_url(next):
        return abort(400)
    else:
        next = next or url_for('admin.collections')

    db.session.delete(collection)
    HistoryItem.build_for(collection)
    db.session.commit()
    return redirect(next)


@bp.route('/collections', methods=['GET'])
def collections():
    return render_template(
        'admin/collections.html',
        title="Collections - Admin",
        collection_table=CollectionTable()
    )


@bp.route('/historyitems', methods=['GET'])
@bp.route('/historyitems/<discriminator>', methods=['GET'])
def historyitems(discriminator=None):
    if discriminator is not None and discriminator not in HISTORY_DISCRIMINATOR_MAP:
        return abort(404)
    return render_template(
        'admin/historyitems.html',
        title="History - Admin",
        historyitem_table=HistoryItemTable(),
        discriminator=discriminator
    )
