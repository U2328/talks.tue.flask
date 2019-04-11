from datetime import datetime

import mistune
from sqlalchemy import and_, false
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin

from app import db, login, db_activity


__all__ = (
    'Collection',
    'Talk',
    'Tag',
    'User',
    'AnonymousUser',
)


class User(UserMixin, db.Model):
    __versioned__ = {}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(128))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def __str__(self):
        return self.username

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
        }


class AnonymousUser(AnonymousUserMixin):
    def get_related(self, model):
        return model.query.filter(false())

    def get_related_with_perms(self, model, *perms, any_=False):
        return model.query.filter(false())

    is_admin = False


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


login.anonymous_user = AnonymousUser


class Talk(db.Model):
    __versioned__ = {}
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now())
    speaker_name = db.Column(db.String(64))
    speaker_aboutme = db.Column(db.Text)
    tags = db.relationship("Tag", secondary=lambda: talk_tags, backref=db.backref('talks'))
    collections = db.relationship("Collection", secondary=lambda: talk_collections, backref=db.backref('talks'))

    def serialize(self, *, recursive=True, exclude=[]):
        data = {
            "id": self.id,
            "title": self.title,
            "timestamp": self.timestamp,
            "description": self.description,
            "rendered_description": mistune.markdown(self.description or ""),
            "speaker_name": self.speaker_name,
            "speaker_aboutme": self.speaker_aboutme,
            "rendered_speaker_aboutme": mistune.markdown(self.speaker_aboutme or ""),
            "tags": (
                [tag.serialize(recursive=False)for tag in self.tags]
                if recursive else
                [tag.name for tag in self.tags]
            ),
            "rendered_tags": ' '.join(tag.render() for tag in self.tags)
        }
        return {key: value for key, value in data.items() if key not in exclude}

    def __hash__(self):
        return hash(str(self.serialize(recursive=False)) + (self.password_hash or ""))


class Collection(db.Model):
    __versioned__ = {}
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    description = db.Column(db.Text)
    is_meta = db.Column(db.Boolean, default=False)
    meta_collections = db.relationship(
        "Collection",
        secondary=lambda: meta_collection_connections,
        primaryjoin=lambda: Collection.id == meta_collection_connections.c.sub_collection_id,
        secondaryjoin=lambda: and_(Collection.id == meta_collection_connections.c.meta_collection_id, Collection.is_meta == True),
        backref=db.backref('sub_collections')
    )

    def __str__(self):
        return self.title

    def serialize(self, *, recursive=True, exclude=[]):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "rendered_description": mistune.markdown(self.description or ""),
            "talks": (
                [talk.serialize(recursive=False) for talk in self.talks]
                if recursive else
                [talk.title for talk in self.talks]
            ),
        }
        return {key: value for key, value in data.items() if key not in exclude}


meta_collection_connections = db.Table('meta_collection_connections',
    db.Column('sub_collection_id', db.Integer, db.ForeignKey('collection.id'), primary_key=True),
    db.Column('meta_collection_id', db.Integer, db.ForeignKey('collection.id'), primary_key=True),
)


talk_collections = db.Table('talk_collections',
    db.Column('talk_id', db.Integer, db.ForeignKey('talk.id'), primary_key=True),
    db.Column('collection_id', db.Integer, db.ForeignKey('collection.id'), primary_key=True),
)


class Tag(db.Model):
    __versioned__ = {}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))

    def get_related(self):
        return self.talks

    def __str__(self):
        return self.name

    def render(self):
        return self.name

    def serialize(self, *, recursive=True, exclude=[]):
        data = {
            "id": self.id,
            "name": self.name,
            "talks": (
                [talk.serialize(recursive=False) for talk in self.talks]
                if recursive else
                [talk.id for talk in self.talks]
            )
        }
        return {key: value for key, value in data.items() if key not in exclude}


talk_tags = db.Table('talk_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('talk_id', db.Integer, db.ForeignKey('talk.id'), primary_key=True),
)

# Activity = db_activity.activity_cls
