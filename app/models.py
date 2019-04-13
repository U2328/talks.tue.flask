from datetime import datetime

from sqlalchemy import and_, false, orm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from flask_pagedown.widgets import PageDown
from flask_babel import lazy_gettext as _l

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
    is_organizer = db.Column(db.Boolean, default=False)
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


class Subscription(db.Model):
    __versioned__ = {}
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'))
    collection = db.relationship('Collection', backref=db.backref('subscriptions'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('subscriptions'))
    remind_me = db.Column(db.Boolean, default=True)


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
    description = db.Column(db.Text, info={'widget': PageDown})
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now())
    speaker_name = db.Column(db.String(64))
    speaker_aboutme = db.Column(db.Text, info={'widget': PageDown})
    tags = db.relationship("Tag", secondary=lambda: talk_tags, backref=db.backref('talks'))
    collections = db.relationship("Collection", secondary=lambda: talk_collections, backref=db.backref('talks'))

    @property
    def rendered_tags(self):
        return ' '.join(tag.render() for tag in self.tags)


class Collection(db.Model):
    __versioned__ = {}
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    description = db.Column(db.Text, info={'widget': PageDown})
    is_meta = db.Column(db.Boolean, default=False)
    meta_collections = db.relationship(
        "Collection",
        secondary=lambda: meta_collection_connections,
        primaryjoin=lambda: Collection.id == meta_collection_connections.c.sub_collection_id,
        secondaryjoin=lambda: and_(Collection.id == meta_collection_connections.c.meta_collection_id, Collection.is_meta == True),
        backref=db.backref('sub_collections')
    )
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    organizer = db.relationship("User", primaryjoin=lambda: and_(User.id == Collection.organizer_id, User.is_organizer == True))
    editors = db.relationship("User", secondary=lambda: collection_editors, backref=db.backref('edited_talks'))

    def __str__(self):
        return self.title


meta_collection_connections = db.Table('meta_collection_connections',
    db.Column('sub_collection_id', db.Integer, db.ForeignKey('collection.id'), primary_key=True),
    db.Column('meta_collection_id', db.Integer, db.ForeignKey('collection.id'), primary_key=True),
)


talk_collections = db.Table('talk_collections',
    db.Column('talk_id', db.Integer, db.ForeignKey('talk.id'), primary_key=True),
    db.Column('collection_id', db.Integer, db.ForeignKey('collection.id'), primary_key=True),
)


collection_editors = db.Table('collection_editors',
    db.Column('collection_id', db.Integer, db.ForeignKey('collection.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
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


talk_tags = db.Table('talk_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('talk_id', db.Integer, db.ForeignKey('talk.id'), primary_key=True),
)

orm.configure_mappers()
Activity = db_activity.activity_cls
