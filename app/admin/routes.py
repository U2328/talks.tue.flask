from flask import render_template, request, redirect, url_for, abort, current_app
from flask_login import current_user, login_required
from sqlalchemy import or_

from . import bp
from .forms import TalkForm, TagForm, CollectionForm, UserForm
from app import db
from app.utils import is_safe_url, copy_row
from app.api.tables import TalkTable, CollectionTable, HistoryItemTable, UserTable
from app.models import (
    HistoryItem,
    HISTORY_DISCRIMINATOR_MAP,
    Tag,
    Talk,
    Collection,
    User,
)


__all__ = ("tag", "talk")


@bp.route("/historyitems", methods=["GET"])
@bp.route("/historyitems/<discriminator>", methods=["GET"])
@login_required
def historyitems(discriminator=None):
    if discriminator is not None and discriminator not in HISTORY_DISCRIMINATOR_MAP:
        return abort(404)
    return render_template(
        "admin/historyitems.html",
        title="History - Admin",
        historyitem_table=HistoryItemTable(),
        discriminator=discriminator,
    )


@bp.route("/tag", methods=["POST"])
def tag():
    if not current_user.is_admin:
        return abort(403)
    form = TagForm(request.form)
    if form.validate_on_submit():
        tag = Tag()
        form.populate_obj(tag)
        db.session.add(tag)
        db.session.commit()
    next = request.args.get("next")
    if not is_safe_url(next):
        return abort(400)
    return redirect(next or url_for("core.index"))


@bp.route("/talk", methods=["GET", "POST"])
@bp.route("/talk/<int:id>", methods=["GET", "POST"])
@login_required
def talk(id=None):
    talk = Talk() if id is None else Talk.query.get(id)

    if id is not None and talk is None:
        return abort(404)
    if not current_user.is_admin and (
        id is not None
        and not talk.can_edit(current_user)
        or len(current_user.edited_collections) == 0
    ):
        return abort(403)
    if request.args.get("copy", False):
        talk = copy_row(talk, ["id"])

    next = request.args.get("next")
    if not is_safe_url(next):
        return abort(400)
    else:
        next = next or url_for("admin.talks")

    is_new = talk.id is None
    form = TalkForm(obj=talk)

    if form.validate_on_submit():
        form.populate_obj(talk)
        HistoryItem.build_for(talk)
        if is_new:
            db.session.add(talk)
        db.session.commit()
        return redirect(next)

    return render_template(
        "admin/talk.html",
        title="Talk - Admin",
        form=form,
        new=is_new,
        next=next,
        talk=talk,
    )


@bp.route("/talk/<int:id>/delete", methods=["GET", "POST"])
@login_required
def delete_talk(id):
    talk = Talk.query.get(id)

    if talk is None:
        return abort(404)
    if not (talk.can_edit(current_user) or current_user.is_admin):
        return abort(403)

    next = request.args.get("next")
    if not is_safe_url(next):
        return abort(400)
    else:
        next = next or url_for("admin.talks")

    db.session.delete(talk)
    HistoryItem.build_for(talk)
    db.session.commit()
    return redirect(next)


@bp.route("/talks", methods=["GET"])
@login_required
def talks():
    if not current_user.can_edit:
        return abort(403)
    filters = []
    if not current_user.is_admin:
        filters.append(
            Talk.collections.any(Collection.editors.any(User.id == current_user.id))
        )
        if current_user.is_organizer:
            filters.append(Talk.collections.any(Collection.organizer == current_user))
    return render_template(
        "admin/talks.html",
        title="Talks - Admin",
        talk_table=TalkTable(query=Talk.query.filter(or_(*filters))),
    )


@bp.route("/collection", methods=["GET", "POST"])
@bp.route("/collection/<int:id>", methods=["GET", "POST"])
@login_required
def collection(id=None):
    collection = Collection() if id is None else Collection.query.get(id)
    can_create = current_user.is_organizer or current_user.is_admin

    if collection is None and id is not None:
        # id given but talk not found
        return abort(404)
    if (
        id is not None
        and not collection.can_edit(current_user)
        or id is None
        and not can_create
    ):
        # id given but can't edit + id not given but can create
        return abort(403)

    if request.args.get("copy", False):
        collection = copy_row(collection, ["id"])

    next = request.args.get("next")
    if not is_safe_url(next):
        return abort(400)
    else:
        next = next or url_for("admin.collections")

    is_new = collection.id is None
    if is_new:
        collection.organizer = current_user
    has_full_access = current_user.is_admin or collection.organizer == current_user
    form = CollectionForm(obj=collection)
    if not has_full_access:
        del form["editors"]
        del form["organizer"]
        del form["is_meta"]
        del form["meta_collections"]

    if form.validate_on_submit():
        form.populate_obj(collection)
        HistoryItem.build_for(collection)
        if is_new:
            db.session.add(collection)
        db.session.commit()
        return redirect(next)

    return render_template(
        "admin/collection.html",
        title="Collection - Admin",
        form=form,
        new=is_new,
        has_full_access=has_full_access,
        next=next,
        collection=collection,
    )


@bp.route("/collection/<int:id>/delete", methods=["GET", "POST"])
@login_required
def delete_collection(id):
    collection = Collection.query.get(id)

    if collection is None:
        return abort(404)
    if not (collection.organizer == current_user or current_user.is_admin):
        return abort(403)

    next = request.args.get("next")
    if not is_safe_url(next):
        return abort(400)
    else:
        next = next or url_for("admin.collections")

    db.session.delete(collection)
    HistoryItem.build_for(collection)
    db.session.commit()
    return redirect(next)


@bp.route("/collections", methods=["GET"])
@login_required
def collections():
    if not current_user.can_edit:
        return abort(403)
    filters = []
    if not current_user.is_admin:
        filters.append(Collection.editors.any(User.id == current_user.id))
        if current_user.is_organizer:
            filters.append(Collection.organizer == current_user)
    return render_template(
        "admin/collections.html",
        title="Collections - Admin",
        collection_table=CollectionTable(query=Collection.query.filter(or_(*filters))),
    )


@bp.route("/user", methods=["GET", "POST"])
@bp.route("/user/<int:id>", methods=["GET", "POST"])
@login_required
def user(id=None):
    if id is None:
        return abort(404)
    if not current_user.is_admin:
        return abort(403)

    user = User.query.get(id)
    if user is None:
        return abort(404)

    next = request.args.get("next")
    if not is_safe_url(next):
        return abort(400)
    else:
        next = next or url_for("admin.users")

    form = UserForm(obj=user)

    if form.validate_on_submit():
        form.populate_obj(user)
        db.session.commit()
        return redirect(next)

    current_app.logger.error(form.errors.values())

    return render_template(
        "admin/user.html", title="User - Admin", form=form, next=next, user=user
    )


@bp.route("/users", methods=["GET"])
@login_required
def users(discriminator=None):
    if not current_user.is_admin:
        return abort(403)
    return render_template(
        "admin/users.html", title="Users - Admin", user_table=UserTable()
    )
