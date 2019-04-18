from flask import jsonify, request, abort, render_template
from flask_babel import lazy_gettext as _l
from flask_login import current_user

from app import db
from app.models import Talk, Tag, Collection, User, HistoryItem, HISTORY_DISCRIMINATOR_MAP
from app.auth.utils import has_perms
from . import bp
from .dt_tools import ModelDataTable


__all__ = (
    'talk',       'talks',       'talk_table',        'TalkTable',         # noqa: E241
    'collection', 'collections', 'collection_table',  'CollectionTable',   # noqa: E241
                                 'tag_table',         'TagTable',          # noqa: E241
                                 'historyitem_table', 'HistoryItemTable',  # noqa: E241
)


@bp.route('/talk', methods=['GET', 'DELETE'])
@bp.route('/talk/<int:id>', methods=['GET', 'DELETE'])
def talk(id=None):
    if id is None:
        id = request.args.get('id')
    if Talk.query.get(id) is None:
        return abort(404)
    if request.method == 'DELETE':
        if not has_perms('admin'):
            raise abort(403)
        Talk.query.filter_by(id=id).delete()
        db.session.commit()
        return jsonify({"message": f"Deleted Talk with id = {id}"})
    else:
        return jsonify(Talk.query.filter(Talk.id == id)[0].serialize())


@bp.route('/talks', methods=['GET'])
def talks():
    return jsonify([talk.serialize() for talk in Talk.query])


class TalkTable(ModelDataTable):
    model = Talk
    cols = [
        {
            'field': 'title',
            'name': _l('Name'),
        }, {
            'field': 'timestamp',
            'name': _l('Date/Time'),
            'weight': 0,
            'render': 'function(data, type, row) {return moment(data).calendar();}',
        }, {
            'field': 'speaker_name',
            'name': _l('Speaker\'s Name'),
        }, {
            'field': 'tags',
            'name': _l('Tags'),
            'orderable': False,
            'value': lambda talk: talk.rendered_tags,
        }
    ]


@bp.route('/talk_table', methods=['GET'])
def talk_table():
    table = TalkTable()
    return table.get_response()


class TagTable(ModelDataTable):
    model = Tag
    cols = [
        {
            'field': 'name',
            'name': _l('Name'),
        }, {
            'field': 'num_of_talks',
            'value': lambda tag: len(tag.talks),
            'orderable': False,
            'name': _l('# Talks'),
        }
    ]


@bp.route('/tag_table', methods=['GET'])
def tag_table():
    table = TagTable()
    return table.get_response()


@bp.route('/collection', methods=['GET', 'DELETE'])
@bp.route('/collection/<int:id>', methods=['GET', 'DELETE'])
def collection(id=None):
    if id is None:
        id = request.args.get('id')
    if Collection.query.get(id) is None:
        return abort(404)
    if request.method == 'DELETE':
        if not has_perms('admin'):
            raise abort(403)
        Collection.query.filter_by(id=id).delete()
        db.session.commit()
        return jsonify({"message": f"Deleted collection with id = {id}"})
    else:
        return jsonify(Collection.query.filter(Collection.id == id)[0].serialize())


@bp.route('/collections', methods=['GET'])
def collections():
    return jsonify([Collection.serialize() for Collection in Collection.query])


class CollectionTable(ModelDataTable):
    model = Collection
    cols = [
        {
            'field': 'title',
            'name': _l('Name'),
        }, {
            'field': 'subscribers',
            'name': _l('# Subscribers'),
            'value': lambda collection: collection.subscriptions.count(collection.subscriptions)
        }
    ]


@bp.route('/collection_table', methods=['GET'])
def collection_table():
    table = CollectionTable()
    return table.get_response()


@bp.route('/admin_collection_table', methods=['GET'])
def admin_collection_table():
    table = CollectionTable(query=Collection.related_to(current_user))
    return table.get_response()


class HistoryItemTable(ModelDataTable):
    model = HistoryItem
    cols = [
        {
            'field': 'timestamp',
            'name': _l('Timestamp')
        }, {
            'field': 'rendered_action',
            'name': _l('Action'),
        }, {
            'field': 'target_id',
            'name': _l('Target'),
            'value': lambda historyitem: (
                f'<a href="{historyitem.get_target_url()}">{historyitem.target_discriminator} #{historyitem.target_id}</a>'
                if historyitem.target is not None else
                historyitem.target_discriminator
            )
        }, {
            'field': 'user',
            'name': _l('User'),
            'orderable': False,
            'value': lambda historyitem: historyitem.user.username,
        }, {
            'field': 'rendered_diff',
            'name': _l('Changes'),
            'orderable': False,
        }
    ]


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


class UserTable(ModelDataTable):
    model = User
    cols = [
        {
            'field': 'username',
            'name': _l('Username')
        }, {
            'field': 'email',
            'name': _l('Email'),
        }, {
            'field': 'is_admin',
            'name': _l('Is Admin?'),
        }, {
            'field': 'is_organizer',
            'name': _l('Is Organizer?'),
        },
    ]


@bp.route('/user_table', methods=['GET'])
def user_table(discriminator=None):
    if not current_user.is_admin:
        return abort(403)
    table = UserTable()
    return table.get_response()
