from functools import wraps

from flask import abort, current_app
from flask_login import current_user


__all__ = (
    'has_perms',
)


def has_perms(*permissions, any_=False):
    def _has_perms(func):
        @wraps(func)
        def _wrapped(*args, **kwargs):
            if current_user.is_authenticated:
                if current_user.has_perms(*permissions, any_=any_):
                    current_app.logger.info(f'User {current_user.username} cleared check for {list(permissions)} on {func.__name__}')
                    return func(*args, **kwargs)
            return abort(403)
        return _wrapped
    return _has_perms
