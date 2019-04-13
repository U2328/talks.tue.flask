from flask import jsonify, request, abort, current_app
from flask_babel import lazy_gettext as _l
from sqlalchemy import or_

from app import db
from app.models import Talk, Tag, Collection
from app.auth.utils import has_perms
from . import bp
from .dt_tools import ModelDataTable


__all__ = (
    'talk',       'talks',       'talk_table',       'TalkTable',        # noqa: E241
    'collection', 'collections', 'collection_table', 'CollectionTable',  # noqa: E241
                                 'tag_table',        'TagTable'          # noqa: E241
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
    return jsonify([talk.serialize() for talk in Talk.query.all()])


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

    def filter(self, value):
        return or_(
            self.model.title.contains(value),
            self.model.tags.any(Tag.name.contains(value)),
        )


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
    return jsonify([Collection.serialize() for Collection in Collection.query.all()])


class CollectionTable(ModelDataTable):
    model = Collection
    cols = [
        {
            'field': 'title',
            'name': _l('Name'),
        }
    ]

    def filter(self, value):
        return or_(
            self.model.title.contains(value),
        )


@bp.route('/collection_table', methods=['GET'])
def collection_table():
    table = CollectionTable()
    return table.get_response()
