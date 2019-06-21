from flask_babel import lazy_gettext as _l

from .dt_tools import ModelDataTable
from app.models import Talk, Tag, Collection, User, HistoryItem
from app.filters import render_bool, render_datetime


__all__ = ("TalkTable", "CollectionTable", "TagTable", "HistoryItemTable", "UserTable")


class TalkTable(ModelDataTable):
    model = Talk
    cols = [
        {"field": "title", "name": _l("Name")},
        {"field": "speaker_name", "name": _l("Speaker")},
        {
            "field": "start_timestamp",
            "name": _l("Starting date"),
            "weight": 0,
            "value": lambda talk: render_datetime(talk.start_timestamp),
        },
        {
            "field": "end_timestamp",
            "name": _l("Ending date"),
            "weight": 0,
            "value": lambda talk: render_datetime(talk.end_timestamp),
        },
        {"field": "location", "name": _l("Location")},
    ]


class CollectionTable(ModelDataTable):
    model = Collection
    cols = [
        {"field": "title", "name": _l("Name")},
        {
            "field": "subscribers",
            "name": _l("# Subscribers"),
            "value": lambda collection: collection.subscriptions.count(
                collection.subscriptions
            ),
        },
    ]


class TagTable(ModelDataTable):
    model = Tag
    cols = [
        {"field": "name", "name": _l("Name")},
        {
            "field": "num_of_talks",
            "value": lambda tag: len(tag.talks),
            "orderable": False,
            "name": _l("# Talks"),
        },
    ]


class HistoryItemTable(ModelDataTable):
    model = HistoryItem
    cols = [
        {"field": "timestamp", "name": _l("Timestamp")},
        {"field": "rendered_action", "name": _l("Action")},
        {
            "field": "target_id",
            "name": _l("Target"),
            "value": lambda historyitem: (
                f'<a href="{historyitem.get_target_url()}">{historyitem.target_discriminator} #{historyitem.target_id}</a>'
                if historyitem.target is not None
                else historyitem.target_discriminator
            ),
        },
        {
            "field": "user",
            "name": _l("User"),
            "orderable": False,
            "value": lambda historyitem: historyitem.user.display_name,
        },
        {"field": "rendered_diff", "name": _l("Changes"), "orderable": False},
    ]


class UserTable(ModelDataTable):
    model = User
    cols = [
        {"field": "display_name", "name": _l("Display name")},
        {"field": "email", "name": _l("Email")},
        {
            "field": "is_admin",
            "name": _l("Is Admin?"),
            "filterable": False,
            "value": lambda user: render_bool(user.is_admin),
        },
        {
            "field": "is_organizer",
            "name": _l("Is Organizer?"),
            "filterable": False,
            "value": lambda user: render_bool(user.is_organizer),
        },
    ]
