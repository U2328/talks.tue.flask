from flask_babel import lazy_gettext as _l

from .dt_tools import ModelDataTable
from app.models import Talk, Tag, Collection, User, HistoryItem


__all__ = (
    'TalkTable',
    'CollectionTable',
    'TagTable',
    'HistoryItemTable',
    'UserTable',
)


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
