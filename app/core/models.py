from datetime import datetime

import mistune
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.associationproxy import association_proxy

from app import db


__all__ = (
    'Speaker',
    'Talk',
    'Tag',
)


class Speaker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    familiy_name = db.Column(db.String(64))
    familiy_name_first = db.Column(db.Boolean, default=False)
    about_me = db.Column(db.Text)
    password_hash = db.Column(db.String(128))

    @property
    def full_name(self):
        return '{} {}'.format(*[*(
            (self.family_name, self.name)
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
            "rendered_about_me": mistune.markdown(self.about_me),
            "talks": (
                [talk.serialize(recursive=False) for talk in self.talks]
                if recursive else
                [talk.id for talk in self.talks]
            )
        }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Talk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now())
    description = db.Column(db.Text)
    speaker_id = db.Column(db.Integer, db.ForeignKey('speaker.id'))
    speaker = db.relationship('Speaker', backref='talks')
    tags = db.relationship("Tag", secondary=lambda: talk_tags, backref=db.backref('talks'))

    def serialize(self, *, recursive=True):
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "description": self.description,
            "rendered_description": mistune.markdown(self.description), 
            "speaker": self.speaker.serialize(recursive=False) if recursive and self.speaker else self.speaker_id,
            "tags": [tag.serialize(recursive=False) for tag in self.tags],
            "rendered_tags": ' '.join(tag.render() for tag in self.tags)
        }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Tag(db.Model):
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
