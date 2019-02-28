from flask_login import current_user

from .models import HistoryItem
from app import db


__all__ = (
    'add_historyitem',
)


def add_historyitem(obj, message, type):
    if not hasattr(obj, 'history'):
        raise TypeError(f"Objects of type {obj.__class__} don't support history items.")
    if not isinstance(type, HistoryItem.Types):
        raise TypeError(f"Historyitems type must be a value of the enum HistoryItem.Types")
    obj.history.append(HistoryItem(
        user=current_user if current_user.is_authenticated else None,
        type=type,
        message=message
    ))
