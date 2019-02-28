from flask import jsonify, request, abort
from flask_babel import lazy_gettext as _l
from sqlalchemy import or_

from app import db
from app.core.models import Talk, Speaker, Tag
from app.auth.utils import has_perms
from . import bp
from .dt_tools import DataTable


__all__ = (
    'talk',    'talks',    'talk_table',    'TalkTable',     # noqa: E241
    'speaker', 'speakers', 'speaker_table', 'SpeakerTable',  # noqa: E241
                           'tag_table',     'TagTable'       # noqa: E241
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


class TalkTable(DataTable):
    model = Talk
    cols = [
        {
            'col': 0,
            'field': 'name',
            'name': _l('Name'),
        }, {
            'col': 1,
            'field': 'timestamp',
            'name': _l('Date/Time'),
            'weight': 0,
            'render': 'function(data, type, row) {return moment(data).calendar();}'
        }, {
            'col': 2,
            'field': 'rendered_tags',
            'name': _l('Tags'),
            'orderable': False,
        }
    ]

    def filter(self, value):
        return or_(
            self.model.name.contains(value),
            self.model.tags.any(Tag.name.contains(value)),
        )

    def filter_values(self, value):
        return lambda talk: value in str(talk.timestamp)


@bp.route('/talk_table', methods=['GET'])
def talk_table():
    table = TalkTable()
    return table.get_response()


@bp.route('/speaker', methods=['GET', 'DELETE'])
@bp.route('/speaker/<int:id>', methods=['GET', 'DELETE'])
def speaker(id=None):
    if id is None:
        id = request.args.get('id')
    if Speaker.query.get(id) is None:
        return abort(404)
    if request.method == 'DELETE':
        if not has_perms('admin'):
            raise abort(403)
        Speaker.query.filter_by(id=id).delete()
        db.session.commit()
        return jsonify({"message": f"Deleted Speaker with id = {id}"})
    else:
        return jsonify(Speaker.query.get(id).serialize())


@bp.route('/speakers', methods=['GET'])
def speakers():
    return jsonify([speaker.serialize() for speaker in Speaker.query.all()])


class SpeakerTable(DataTable):
    model = Speaker
    cols = [
        {
            'col': 0,
            'field': 'full_name',
            'name': _l('Name'),
            'custom_order': lambda dir: (getattr(Speaker.name, dir)(), getattr(Speaker.familiy_name, dir)()),
            'custom_filter': lambda value: or_(Speaker.name.contains(value), Speaker.familiy_name.contains(value)),
        }
    ]


@bp.route('/speaker_table', methods=['GET'])
def speaker_table():
    table = SpeakerTable()
    return table.get_response()


class TagTable(DataTable):
    model = Tag
    cols = [
        {
            'col': 0,
            'field': 'name',
            'name': _l('Name'),
        }
    ]


@bp.route('/tag_table', methods=['GET'])
def tag_table():
    table = TagTable()
    return table.get_response()
