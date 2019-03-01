from datetime import datetime
from collections import namedtuple
from enum import Enum, unique, auto

import mistune
from flask import current_app
from flask_babel import lazy_gettext as _l
from sqlalchemy import and_, event
from sqlalchemy.orm import foreign, backref, remote
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.utils import DotDict


__all__ = (
    'HistoryItem'
    'Speaker',
    'Talk',
    'Tag',
)


HistoryItemType = namedtuple('HistoryItemType', ('icon', 'template'))


class HistoryItem(db.Model):
    @unique
    class Types(Enum):
        MISC   = HistoryItemType(  # noqa: E221
            'fas fa-feather-alt text-info',
            lambda obj: _l('%(message)s', message=obj.message)
        )
        CREATE = HistoryItemType(
            'fas fa-plus-circle text-success',
            lambda obj: _l('%(user)s created %(desc)s #%(id)d', user=obj.user, desc=obj.target_discriminator, id=int(obj.target_id))
        )
        EDIT   = HistoryItemType(  # noqa: E221
            'fa fa-edit text-warning',
            lambda obj: _l('%(user)s edited %(desc)s #%(id)d', user=obj.user, desc=obj.target_discriminator, id=int(obj.target_id))
        )
        DELETE = HistoryItemType(
            'far fa-trash-alt text-danger',
            lambda obj: _l('%(user)s deleted %(desc)s #%(id)d', user=obj.user, desc=obj.target_discriminator, id=int(obj.target_id))
        )

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(Types))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship("User", backref='history')
    message = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now())

    target_discriminator = db.Column(db.String())
    target_id = db.Column(db.Integer())

    @property
    def target(self):
        return getattr(self, f"target_{self.target_discriminator}")

    def render_message(self):
        return f"<i class='{self.type.value.icon}'></i> {self.type.value.template(self)}"

    def serialize(self, *, recursive=True):
        return {
            "id": self.id,
            "type": self.type,
            "user": self.user.serialize(),
            "message": self.message,
            "timestamp": self.timestamp,
            "target": (
                self.target.serialize(recursive=False)
                if recursive else
                {
                    "type": self.target_discriminator,
                    "id": self.target_id
                }
            )
        }


class HasHistory: ...  # noqa: E701


@event.listens_for(HasHistory, "mapper_configured", propagate=True)
def setup_listener(mapper, class_):
    discriminator = class_.__name__.lower()
    class_.history = db.relationship(
        HistoryItem,
        primaryjoin=and_(
            class_.id == foreign(remote(HistoryItem.target_id)),
            HistoryItem.target_discriminator == discriminator,
        ),
        backref=backref(
            f"target_{discriminator}",
            primaryjoin=remote(class_.id) == foreign(HistoryItem.target_id),
        ),
    )

    @event.listens_for(class_.history, "append")
    def append_history(self, history_item, event):
        history_item.target_discriminator = discriminator


class Speaker(HasHistory, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    viewable = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    familiy_name = db.Column(db.String(64))
    familiy_name_first = db.Column(db.Boolean, default=False)
    about_me = db.Column(db.Text)
    password_hash = db.Column(db.String(128))

    @classmethod
    def query_viewable(cls):
        return cls.query.filter_by(viewable=True)

    @property
    def full_name(self):
        return '{} {}'.format(*[*(
            (self.familiy_name, self.name)
            if self.familiy_name_first else
            (self.name, self.familiy_name)
        )])

    def __str__(self):
        return self.full_name

    def serialize(self, *, recursive=True):
        return {
            "id": self.id,
            "name": self.name,
            "familiy_name": self.familiy_name,
            'full_name': self.full_name,
            "about_me": self.about_me,
            "rendered_about_me": mistune.markdown(self.about_me or ""),
            "talks": (
                [talk.serialize(recursive=False) for talk in self.talks]
                if recursive else
                [talk.id for talk in self.talks]
            )
        }

    def __hash__(self):
        return hash(str(self.serialize(recursive=False)) + (self.password_hash or ""))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Talk(HasHistory, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    viewable = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now())
    description = db.Column(db.Text)
    speaker_id = db.Column(db.Integer, db.ForeignKey('speaker.id'))
    speaker = db.relationship('Speaker', backref='talks')
    tags = db.relationship("Tag", secondary=lambda: talk_tags, backref=db.backref('talks'))

    @classmethod
    def query_viewable(cls):
        return cls.query.filter_by(viewable=True)

    def serialize(self, *, recursive=True):
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "description": self.description,
            "rendered_description": mistune.markdown(self.description or None),
            "speaker": self.speaker.serialize(recursive=False) if recursive and self.speaker else self.speaker_id,
            "tags": [tag.serialize(recursive=False) for tag in self.tags],
            "rendered_tags": ' '.join(tag.render() for tag in self.tags)
        }

    def __hash__(self):
        return hash(str(self.serialize(recursive=False)) + (self.password_hash or ""))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Tag(HasHistory, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))

    def __str__(self):
        return self.name

    def render(self):
        return self.name

    def serialize(self, *, recursive=True):
        return {
            "id": self.id,
            "name": self.name,
            "talks": (
                [talk.serialize(recursive=False) for talk in self.talks]
                if recursive else
                [talk.id for talk in self.talks]
            )
        }


talk_tags = db.Table('talk_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('talk_id', db.Integer, db.ForeignKey('talk.id'), primary_key=True),
)


tag_preferences = db.Table('tag_preferences',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)
