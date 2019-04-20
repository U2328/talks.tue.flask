from datetime import datetime

from flask import abort
from flask_login import current_user, login_required

from .tables import TalkTable, CollectionTable, TagTable, HistoryItemTable, UserTable
from app.models import Talk, Collection, HISTORY_DISCRIMINATOR_MAP
from . import bp


__all__ = (
    'talk_table', 'user_talk_table',
    'collection_table', 'admin_collection_table',
    'tag_table',
    'historyitem_table',
    'user_table',
)


@bp.route('/talk_table', methods=['GET'])
def talk_table():
    table = TalkTable()
    return table.get_response()


@bp.route('/user_talk_table')
@login_required
def user_talk_table():
    subscriptions = current_user.subscriptions
    now = datetime.now()
    talk_ids = list(set(
        talk.id
        for subscription in subscriptions
        for talk in subscription.collection.related_talks
        if talk.timestamp >= now
    ))
    talk_table = TalkTable(
        query=Talk.query.filter(Talk.id.in_(talk_ids))
    )
    return talk_table.get_response()


@bp.route('/collection_table', methods=['GET'])
def collection_table():
    table = CollectionTable()
    return table.get_response()


@bp.route('/admin_collection_table', methods=['GET'])
def admin_collection_table():
    table = CollectionTable(query=Collection.related_to(current_user))
    return table.get_response()


@bp.route('/tag_table', methods=['GET'])
def tag_table():
    table = TagTable()
    return table.get_response()


@bp.route('/historyitem_table', methods=['GET'])
@bp.route('/historyitem_table/<discriminator>', methods=['GET'])
def historyitem_table(discriminator=None):
    if discriminator is not None and discriminator not in HISTORY_DISCRIMINATOR_MAP:
        return abort(404)
    table = HistoryItemTable(query=(
        HISTORY_DISCRIMINATOR_MAP[discriminator].complete_history(user=current_user)
        if discriminator is not None else None
    ))
    return table.get_response()


@bp.route('/user_table', methods=['GET'])
def user_table(discriminator=None):
    if not current_user.is_admin:
        return abort(403)
    table = UserTable()
    return table.get_response()
