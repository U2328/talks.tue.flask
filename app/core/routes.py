from flask import render_template, request, redirect, url_for, abort, current_app
from flask_login import current_user, login_required
from sqlalchemy import or_

from . import bp
from .forms import TalkForm, CollectionForm, UserForm
from app import db
from app.utils import is_safe_url, copy_row
from app.api.tables import TalkTable, CollectionTable, HistoryItemTable, UserTable
from app.models import HistoryItem, HISTORY_DISCRIMINATOR_MAP, Talk, Collection, User


__all__ = (
    "index",
    "talk",
    "edit_talk",
    "delete_talk",
    "talks",
    "editable_talks",
    "collection",
    "edit_collection",
    "delete_collection",
    "collections",
    "editable_collections",
)


@bp.route("/")
@bp.route("/index")
def index():
    talks = Talk.query[:9]
    return render_template("core/index.html", up_next=talks)


#######################
#  TALKS
#######################


@bp.route("/talk")
@bp.route("/talk/<int:id>")
def talk(id=None):
    id = id or request.args.get("id")
    if id is None:
        return abort(404)
    talk = Talk.query.get(id)
    if talk is None:
        return abort(404)
    return render_template(
        "core/talk.html",
        title=talk.title,
        talk=talk,
        can_edit=talk.can_edit(current_user),
    )


@bp.route("/talk/create", methods=["GET", "POST"])
@bp.route("/talk/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_talk(id=None):
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
        next = next or url_for("core.talks")

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
        "core/talk_edit.html", title="Talk", form=form, new=is_new, next=next, talk=talk
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
        next = next or url_for("core.talks")

    db.session.delete(talk)
    HistoryItem.build_for(talk)
    db.session.commit()
    return redirect(next)


@bp.route("/talks")
def talks():
    table = TalkTable()
    return render_template("core/talks.html", title="Talks", table=table)


@bp.route("/talks/editable", methods=["GET"])
@login_required
def editable_talks():
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
        "core/talks.html",
        title="Talks",
        editables=True,
        table=TalkTable(query=Talk.query.filter(or_(*filters))),
    )


#######################
#  COLLECTIONS
#######################


@bp.route("/collection")
@bp.route("/collection/<int:id>")
def collection(id=None):
    id = id or request.args.get("id")
    if id is None:
        return abort(404)
    collection = Collection.query.get(id)
    if collection is None:
        return abort(404)
    return render_template(
        "core/collection.html",
        title=collection.title,
        collection=collection,
        can_edit=collection.can_edit(current_user),
    )


@bp.route("/collection/create", methods=["GET", "POST"])
@bp.route("/collection/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_collection(id=None):
    collection = Collection() if id is None else Collection.query.get(id)
    can_create = current_user.is_organizer or current_user.is_admin

    if collection is None and id is not None:
        return abort(404)
    if (
        id is not None
        and not collection.can_edit(current_user)
        or id is None
        and not can_create
    ):
        return abort(403)

    if request.args.get("copy", False):
        collection = copy_row(collection, ["id"])

    next = request.args.get("next")
    if not is_safe_url(next):
        return abort(400)
    else:
        next = next or url_for("core.collections")

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
        "core/collection_edit.html",
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
        next = next or url_for("core.collections")

    db.session.delete(collection)
    HistoryItem.build_for(collection)
    db.session.commit()
    return redirect(next)


@bp.route("/collections")
def collections():
    table = CollectionTable()
    return render_template("core/collections.html", title="Collections", table=table)


@bp.route("/collections/editable", methods=["GET"])
@login_required
def editable_collections():
    if not current_user.can_edit:
        return abort(403)
    filters = []
    if not current_user.is_admin:
        filters.append(Collection.editors.any(User.id == current_user.id))
        if current_user.is_organizer:
            filters.append(Collection.organizer == current_user)
    return render_template(
        "core/collections.html",
        title="Collections",
        editables=True,
        table=CollectionTable(query=Collection.query.filter(or_(*filters))),
    )


#######################
#  MISC
#######################


@bp.route("/historyitems", methods=["GET"])
@bp.route("/historyitems/<discriminator>", methods=["GET"])
@login_required
def historyitems(discriminator=None):
    if discriminator is not None and discriminator not in HISTORY_DISCRIMINATOR_MAP:
        return abort(404)
    return render_template(
        "core/historyitems.html",
        title="History",
        historyitem_table=HistoryItemTable(),
        discriminator=discriminator,
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
        next = next or url_for("core.users")

    form = UserForm(obj=user)

    if form.validate_on_submit():
        form.populate_obj(user)
        db.session.commit()
        return redirect(next)

    current_app.logger.error(form.errors.values())

    return render_template(
        "core/user_edit.html", title="User - Admin", form=form, next=next, user=user
    )


@bp.route("/users", methods=["GET"])
@login_required
def users(discriminator=None):
    if not current_user.is_admin:
        return abort(403)
    return render_template(
        "core/users.html", title="Users - Admin", user_table=UserTable()
    )
