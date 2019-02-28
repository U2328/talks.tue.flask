from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.ext.associationproxy import association_proxy

from app import db, login
from app.utils import DotDict
from app.core.models import tag_preferences


__all__ = (
    'User',
    'Permission'
)


Permission = DotDict(
    ADMIN=1,
    MODERATE=2,
    FOLLOW=4,
    COMMENT=8,
    WRITE=16,
)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    default = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(32), index=True, unique=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    DEFAULT_ROLE = 'user'
    ROLE_DEFINITIONS = {
        'user': [
            Permission.FOLLOW,
            Permission.COMMENT,
            Permission.WRITE
        ],
        'moderator': [
            Permission.FOLLOW,
            Permission.COMMENT,
            Permission.WRITE,
            Permission.MODERATE
        ],
        'admin': [
            Permission.FOLLOW,
            Permission.COMMENT,
            Permission.WRITE,
            Permission.MODERATE,
            Permission.ADMIN
        ],
    }

    def has_perms(self, *permissions, any_=True):
        if not all(perm in Permission.values() for perm in permissions):
            raise TypeError("Only permissions from the Permissions DotDict can be used.")
        return (
            any and any(perm & self.permissions == perm for perm in permissions) or
            all(perm & self.permissions == perm for perm in permissions)
        )

    def add_perm(self, perm):
        if not self.has_perms(perm):
            self.permissions += perm

    def add_perms(self, *perms):
        for perm in perms:
            self.add_perm(perm)

    def remove_perm(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_perms(self):
        self.permissions = 0

    def serialize(self, *, recursive=True):
        return {
            "id": self.id,
            "name": self.name,
            "permissions": self.permissions,
            "users": [
                [_.serialize(recursive=False) for _ in self.users]
                if recursive else
                [_.id for _ in self.users]
            ]
        }

    @classmethod
    def insert_roles(cls, roles=None):
        roles = roles or cls.ROLE_DEFINITIONS
        default_role = cls.DEFAULT_ROLE
        for r in roles:
            role = cls.query.filter_by(name=r).first() or Role(name=r)
            role.reset_perms()
            role.add_perms(*roles[r])
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    _tag_preferences = db.relationship("Tag", secondary=lambda: tag_preferences)
    tag_preferences = association_proxy('_tag_preferences', 'name')
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            self.role = Role.query.filter_by(default=True).first()

    def __repr__(self):
        return '<User {}>'.format(self.username)
        
    def __str__(self):
        return self.username

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_perms(self, *permissions, any=False):
        return self.role.has_perms(*permissions, any_=any)

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "tag_preferences": list(self.tag_preferences),
            "role": self.role.name,
        }


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
