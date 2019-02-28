from urllib.parse import urlparse, urljoin
from flask import request


__all__ = (
    'is_safe_url',
    'copy_row',
    'DotDict',
)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def copy_row(model, row, ignored_columns=[]):
    copy = model()
    for col in row.__table__.columns:
        if col.name not in ignored_columns:
            try:
                copy.__setattr__(col.name, getattr(row, col.name))
            except Exception as e:
                print(e)
                continue
    return copy


class DotDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
