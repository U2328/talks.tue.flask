from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.ext.associationproxy import association_proxy

from app import db, login
from app.core.models import tag_preferences


__all__ = (
    'User',
    'Permission'
)


class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True, unique=True)


user_permissions = db.Table('user_permissions',
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    _tag_preferences = db.relationship("Tag", secondary=lambda: tag_preferences)
    tag_preferences = association_proxy('_tag_preferences', 'name')
    _permissions = db.relationship("Permission", secondary=lambda: user_permissions)
    permissions = association_proxy('_permissions', 'name')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_perms(self, *permissions, any=False):
        overlap, missing = self.check_perms(*permissions)
        return len(missing) == 0 or any and len(overlap) > 0 

    def check_perms(self, *permissions):
        return (
            [perm for perm in permissions if perm in self.permissions],
            [perm for perm in permissions if perm not in self.permissions]
        )

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "tag_preferences": list(self.tag_preferences),
            "permissions": list(self.permissions),
        }


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
