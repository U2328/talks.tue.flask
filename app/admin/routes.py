from flask import render_template, request, redirect,\
                  url_for, abort, current_app
from flask_login import current_user

from . import bp
from .forms import TalkForm, TagForm, CollectionForm
from app import db
from app.utils import is_safe_url, copy_row
from app.api.routes import TalkTable, TagTable, CollectionTable
from app.models import Talk, Tag, Collection, Activity


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

    if id is not None and not current_user.is_admin:
        return abort(403)
    if talk is None and id is not None:
        return abort(404)
    if request.args.get('copy', False):
        talk = copy_row(talk, ['id'])

    next = request.args.get('next')
    if not is_safe_url(next):
        return abort(400)
    else:
        next = next or url_for('admin.talks')

    is_new = talk.id is None
    current_app.logger.debug(f">>> {talk.timestamp}")
    form = TalkForm(obj=talk)
    current_app.logger.debug(f">>> {form.timestamp()}")

    if form.validate_on_submit():
        form.populate_obj(talk)
        if is_new:
            db.session.add(talk)
        db.session.flush()

        activity = Activity(
            verb='create' if is_new else 'edit',
            object=talk
        )
        db.session.add(activity)
        db.session.commit()
        return redirect(next)

    return render_template('admin/talk.html', title="Talk - Admin", form=form, new=is_new, next=next)


@bp.route('/talk/<int:id>/delete', methods=['GET', 'POST'])
def delete_talk(id):
    talk = Talk.query.get(id)

    if talk is None:
        return abort(404)
    if not current_user.is_admin:
        return abort(403)

    db.session.delete(talk)
    db.session.commit()
    return redirect(url_for('admin.index'))


@bp.route('/talks', methods=['GET'])
def talks():
    return render_template(
        'admin/talks.html',
        title="Talks - Admin",
        talk_table=TalkTable(),
    )


@bp.route('/collection', methods=['GET', 'POST'])
@bp.route('/collection/<int:id>', methods=['GET', 'POST'])
def collection(id=None):
    collection = Collection() if id is None else Collection.query.get(id)

    if id is not None and not current_user.is_admin:
        return abort(403)
    if collection is None and id is not None:
        return abort(404)
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
        db.session.flush()

        activity = Activity(
            verb='create' if is_new else 'edit',
            object=collection
        )
        db.session.add(activity)
        db.session.commit()
        return redirect(next)

    return render_template('admin/collection.html', title="Collection - Admin", form=form, new=is_new, next=next)


@bp.route('/collection/<int:id>/delete', methods=['GET', 'POST'])
def delete_collection(id):
    collection = Collection.query.get(id)

    if collection is None:
        return abort(404)
    if not current_user.is_admin:
        return abort(403)

    db.session.delete(collection)
    db.session.commit()
    return redirect(url_for('admin.index'))


@bp.route('/collections', methods=['GET'])
def collections():
    return render_template(
        'admin/collections.html',
        title="Collections - Admin",
        collection_table=CollectionTable(),
    )
