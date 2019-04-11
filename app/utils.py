from urllib.parse import urlparse, urljoin
from flask import request


__all__ = (
    'is_safe_url',
    'copy_row',
)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def copy_row(row, ignored_columns=[]):
    copy = type(row)()
    for col in row.__table__.columns:
        if col.name not in ignored_columns:
            setattr(copy, col.name, getattr(row, col.name))
    return copy
