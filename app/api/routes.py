from flask import jsonify, request, abort, current_app
from flask_babel import lazy_gettext as _l
from sqlalchemy import or_

from app import db
from app.core.models import Talk, Speaker, Tag, HistoryItem
from app.core.utils import add_historyitem
from app.auth.utils import has_perms
from . import bp
from .dt_tools import DataTable


__all__ = (
    'talk',    'talks',    'talk_table',    'TalkTable',     # noqa: E241
    'speaker', 'speakers', 'speaker_table', 'SpeakerTable',  # noqa: E241
                           'tag_table',     'TagTable'       # noqa: E241
)


@bp.route('/historyitem', methods=['GET'])
@bp.route('/historyitem/<int:id>', methods=['GET'])
def historyitem(id=None):
    if id is None:
        id = request.args.get('id')
    if HistoryItem.query.get(id) is None:
        return abort(404)
    return jsonify(HistoryItem.query.get(id).serialize())


@bp.route('/historyitems', methods=['GET'])
def historyitems():
    return jsonify([historyitem.serialize() for historyitem in HistoryItem.query.all()])


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
        add_historyitem(Talk.query.get(id), '', HistoryItem.Types.DELETE)
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
    query = lambda: Talk.query_viewable()
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
            'render': 'function(data, type, row) {return moment(data).calendar();}',
            'custom_filter': lambda talk, value: current_app.logger.debug(f"{repr(value)} - {talk.timestamp}") or value in str(talk.timestamp),
        }, {
            'col': 2,
            'field': 'rendered_tags',
            'name': _l('Tags'),
            'orderable': False,
            'custom_filter': lambda talk, value: any(value in tag.name for tag in talk.tags),
        }
    ]

    def filter(self, value):
        return or_(
            self.model.name.contains(value),
            self.model.tags.any(Tag.name.contains(value)),
        )


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
        add_historyitem(Speaker.query.get(id), '', HistoryItem.Types.DELETE)
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
    query = lambda: Speaker.query_viewable()
    cols = [
        {
            'col': 0,
            'field': 'full_name',
            'name': _l('Name'),
            'custom_order': lambda dir: (getattr(Speaker.name, dir)(), getattr(Speaker.familiy_name, dir)()),
            'custom_filter': lambda speaker, value: value in speaker.name or value in speaker.familily_name,
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
