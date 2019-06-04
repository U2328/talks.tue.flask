from collections import namedtuple
from datetime import datetime
from enum import IntEnum, unique, auto
from uuid import uuid4

from sqlalchemy import and_, or_, event, inspect
from sqlalchemy.orm import foreign, backref, remote
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, url_for, current_app
from flask_login import UserMixin, AnonymousUserMixin, current_user
from flask_babel import lazy_gettext as _l, gettext as _

from . import db, login, cache
from .utils import DillField


__all__ = (
    "Collection",
    "Talk",
    "Tag",
    "User",
    "AnonymousUser",
    "HistoryItem",
    "HISTORY_DISCRIMINATOR_MAP",
    "Subscription",
)


HistoryItemType = namedtuple(
    "HistoryItemType", ("append_to_obj", "icon", "name", "template")
)


@unique
class HistoryStates(IntEnum):
    CREATE = auto()
    EDIT = auto()  # noqa: E221
    DELETE = auto()

    @classmethod
    def get_type(cls, state):
        return {
            cls.CREATE: HistoryItemType(
                True,
                "green plus circle icon",
                _l("create"),
                lambda history_item: _l(
                    "%(user)s created %(name)s",
                    user=history_item.user,
                    name=repr(history_item.target_name),
                ),
            ),
            cls.EDIT: HistoryItemType(
                True,
                "yellow edit icon",
                _l("edit"),
                lambda history_item: _l(
                    "%(user)s edited %(name)s",
                    user=history_item.user,
                    name=repr(history_item.target_name),
                ),
            ),
            cls.DELETE: HistoryItemType(
                False,
                "red trash alternate icon",
                _l("delete"),
                lambda history_item: _l(
                    "%(user)s deleted %(name)s",
                    user=history_item.user,
                    name=repr(history_item.target_name),
                ),
            ),
        }.get(state)


class HistoryItem(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    _type = db.Column(db.Enum(HistoryStates))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref=backref("history"))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now())
    diff = db.Column(DillField())

    target_discriminator = db.Column(db.String())
    target_id = db.Column(db.Integer())
    target_name = db.Column(db.String())

    @property
    def target(self):
        return getattr(self, f"target_{self.target_discriminator}")

    def get_target_url(self):
        target = self.target
        return target and target.get_absolute_url() or "#"

    @property
    def type(self):
        return HistoryStates.get_type(self._type)

    @property
    def message(self):
        return self.type.template(self)

    @classmethod
    def get_discriminated_model(cls, discriminator):
        return cls.discriminator_map.get(discriminator)

    @property
    def rendered_action(self):
        return f'<span class="badge badge-pill badge-dark"><i class="{self.type.icon}"></i>&nbsp;{self.type.name}</span>'

    @property
    def rendered_diff(self):
        return render_template("snippets/diff.html", diff=self.diff)

    @classmethod
    def build_for(cls, obj, user=None):
        assert isinstance(
            obj, HasHistory
        ), "Can only build historyitems for models that have a history."

        user = user or (current_user if current_user.is_authenticated else None)
        target_discriminator = obj.__class__.history_discriminator

        inspection = inspect(obj)
        diff = dict()
        for attr in inspection.attrs:
            field = attr.key
            if attr.history.has_changes():
                added, unchanged, deleted = attr.history
                diff[field] = {
                    "from": [*deleted, *unchanged] or None,
                    "to": [*added, *unchanged] or None,
                }

        if not inspection.has_identity:
            state = HistoryStates.CREATE
        elif not diff:
            current_app.logger.debug(inspection.identity)
            state = HistoryStates.DELETE
        else:
            state = HistoryStates.EDIT
        hi_type = HistoryStates.get_type(state)

        hi = HistoryItem(
            user=user,
            _type=state,
            diff=diff,
            target_discriminator=target_discriminator,
            target_name=str(obj),
        )
        if hi_type.append_to_obj:
            obj.history.append(hi)
        else:
            db.session.add(hi)
        return hi


HISTORY_DISCRIMINATOR_MAP = dict()


class HasHistory:
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        discriminator = cls.__name__.lower()
        setattr(cls, "history_discriminator", discriminator)
        HISTORY_DISCRIMINATOR_MAP[discriminator] = cls

    @classmethod
    def complete_history(cls, *args, **kwargs):
        return HistoryItem.query.filter(
            HistoryItem.target_discriminator == cls.history_discriminator
        )

    def get_absolute_url(self):
        raise NotImplementedError()


@event.listens_for(HasHistory, "mapper_configured", propagate=True)
def setup_listener(mapper, cls):
    cls.history = db.relationship(
        HistoryItem,
        primaryjoin=and_(
            cls.id == foreign(remote(HistoryItem.target_id)),
            HistoryItem.target_discriminator == cls.history_discriminator,
        ),
        backref=backref(
            f"target_{cls.history_discriminator}",
            primaryjoin=remote(cls.id) == foreign(HistoryItem.target_id),
        ),
    )


class User(UserMixin, db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_organizer = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(128))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return "<User {}>".format(self.username)

    def __str__(self):
        return self.username

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property  # type: ignore
    @cache.memoize(60)
    def upcoming_talks(self):
        now = datetime.now()
        return list(
            set(
                talk
                for subscription in self.subscriptions
                for talk in subscription.collection.related_talks
                if talk.timestamp >= now
            )
        )

    @property
    def can_edit(self):
        return self.is_admin or self.is_organizer or len(self.edited_collections) > 0

    def is_subscribed_to(self, collection):
        return (
            len(
                [
                    subscription
                    for subscription in self.subscriptions
                    if subscription.collection == collection
                ]
            )
            > 0
        )


class Subscription(db.Model):  # type: ignore
    @unique
    class Modes(IntEnum):
        DAILY = auto()
        WEEKLY = auto()
        DAILY_AND_WEEKLY = auto()

        @classmethod
        def coerce(cls, item):
            return item if type(item) == cls else cls(int(item))

        @classmethod
        def choices(cls):
            return [(choice.value, str(choice)) for choice in cls]

        def __str__(self):
            return [_("daily"), _("weekly"), _("daily and weekly")][self.value - 1]

    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey("collection.id"))
    collection = db.relationship("Collection", backref=backref("subscriptions"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref=backref("subscriptions"))
    remind_me = db.Column(db.Boolean, default=True)
    mode = db.Column(db.Enum(Modes), default=Modes.DAILY_AND_WEEKLY)


class AnonymousUser(AnonymousUserMixin):
    is_admin = False
    is_organizer = False
    can_edit = False


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


login.anonymous_user = AnonymousUser


talk_collections = db.Table(
    "talk_collections",
    db.Column("talk_id", db.Integer, db.ForeignKey("talk.id"), primary_key=True),
    db.Column(
        "collection_id", db.Integer, db.ForeignKey("collection.id"), primary_key=True
    ),
)


talk_tags = db.Table(
    "talk_tags",
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
    db.Column("talk_id", db.Integer, db.ForeignKey("talk.id"), primary_key=True),
)


class Talk(HasHistory, db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now())
    speaker_name = db.Column(db.String(64))
    speaker_aboutme = db.Column(db.Text)
    tags = db.relationship("Tag", secondary=lambda: talk_tags, backref=backref("talks"))
    collections = db.relationship(
        "Collection", secondary=lambda: talk_collections, backref=backref("talks")
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return url_for("core.talk", id=self.id)

    @property
    def rendered_tags(self):
        return " ".join(tag.render() for tag in self.tags)

    @classmethod
    def complete_history(cls, user=None):
        if user is None or user.is_admin:
            return super().complete_history()
        else:
            return (
                super()
                .complete_history()
                .join(
                    Talk,
                    and_(
                        HistoryItem.target_discriminator == Talk.history_discriminator,
                        HistoryItem.target_id == Talk.id,
                    ),
                )
                .filter(
                    Talk.collections.any(
                        or_(
                            Collection.organizer == user,
                            Collection.editors.contains(user),
                        )
                    )
                )
            )

    @classmethod
    def related_to(cls, user):
        if user.is_admin:
            return Talk.query
        else:
            return Talk.query.filter(
                Talk.collections.any(
                    or_(Collection.organizer == user, Collection.editors.contains(user))
                )
            )

    def can_edit(self, user):
        return user.is_admin or any(
            user == collection.organizer or user in collection.editors
            for collection in self.collections
        )


meta_collection_connections = db.Table(
    "meta_collection_connections",
    db.Column(
        "sub_collection_id",
        db.Integer,
        db.ForeignKey("collection.id"),
        primary_key=True,
    ),
    db.Column(
        "meta_collection_id",
        db.Integer,
        db.ForeignKey("collection.id"),
        primary_key=True,
    ),
)


collection_editors = db.Table(
    "collection_editors",
    db.Column(
        "collection_id", db.Integer, db.ForeignKey("collection.id"), primary_key=True
    ),
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
)


class Collection(HasHistory, db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    description = db.Column(db.Text)
    is_meta = db.Column(db.Boolean, default=False)
    meta_collections = db.relationship(
        "Collection",
        secondary=lambda: meta_collection_connections,
        primaryjoin=lambda: Collection.id
        == meta_collection_connections.c.sub_collection_id,
        secondaryjoin=lambda: and_(
            Collection.id == meta_collection_connections.c.meta_collection_id,
            Collection.is_meta == True,
        ),
        backref=backref("sub_collections"),
    )
    organizer_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    organizer = db.relationship(
        "User",
        primaryjoin=lambda: and_(
            User.id == Collection.organizer_id, User.is_organizer == True
        ),
    )
    editors = db.relationship(
        "User",
        secondary=lambda: collection_editors,
        backref=backref("edited_collections"),
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return url_for("core.collection", id=self.id)

    @property  # type: ignore
    @cache.memoize(10)
    def related_talks(self):
        if not self.is_meta:
            return self.talks
        else:
            return list(
                set(
                    talk
                    for collection in self.sub_collections
                    for talk in collection.related_talks
                )
            )

    @classmethod
    def complete_history(cls, user=None):
        if user is None or user.is_admin:
            return super().complete_history()
        else:
            return (
                super()
                .complete_history()
                .join(Collection, HistoryItem.target_id == Collection.id)
                .filter(
                    or_(Collection.organizer == user, Collection.editors.contains(user))
                )
            )

    @classmethod
    def related_to(cls, user):
        if user.is_admin:
            return Collection.query
        else:
            return Collection.query.filter(
                or_(Collection.organizer == user, Collection.editors.contains(user))
            )

    def can_edit(self, user):
        return (
            user.is_admin
            or user == self.organizer
            or user in self.editors
            or any(meta.can_edit(user) for meta in self.meta_collections)
        )


class Tag(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))

    def get_related(self):
        return self.talks

    def __str__(self):
        return self.name

    def render(self):
        return self.name


class AccessToken(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(128), unique=True)
    password_hash = db.Column(db.String(128))
    talk_id = db.Column(db.Integer, db.ForeignKey("talk.id"))
    talk = db.relationship("Talk", backref=backref("access_tokens"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uuid = uuid4()
        while AccessToken.objects.filter(AccessToken.uuid == uuid).count() > 0:
            uuid = uuid4()
        self.uuid = uuid

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
