from dateutil.parser import parse as parse_datetime
from flask import jsonify, request, current_app
from sqlalchemy import or_, cast, DateTime

from app import db
from app.core.models import Talk, Speaker, Tag
from . import bp
from .dt_tools import DataTable


@bp.route('/talk', methods=['GET'])
@bp.route('/talk/<int:id>', methods=['GET'])
def talk(id=None):
    if id is None:
        id = request.args.get('id')
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
            'name': 'Name',
            'weight': 1,
        }, {
            'col': 1,
            'field': 'timestamp',
            'name': 'Time',
            'weight': 0,
        }, {
            'col': 2,
            'field': 'tags',
            'name': 'Tags',
            'orderable': False,
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


@bp.route('/speaker', methods=['GET'])
@bp.route('/speaker/<int:id>', methods=['GET'])
def speaker(id=None):
    if id is None:
        id = request.args.get('id')
    return jsonify(Speaker.query.filter(speaker.id == id)[0].serialize())    


@bp.route('/speakers', methods=['GET'])
def speakers():
    return jsonify([speaker.serialize() for speaker in Speaker.query.all()])


class SpeakerTable(DataTable):
    model = Speaker
    cols = [
        {
            'col': 0,
            'field': 'full_name',
            'name': 'Name',
            'custom_order': lambda dir: (getattr(Speaker.name, dir)(), getattr(Speaker.familiy_name, dir)()),
            'custom_filter': lambda value: or_(Speaker.name.contains(value), Speaker.familiy_name.contains(value)),
            'weight': 0,
        }
    ]


@bp.route('/speaker_table', methods=['GET'])
def speaker_table():
    table = SpeakerTable()
    return table.get_response()
