import json as _json
from flask import current_app

__all__ = ("json", "render_bool", "render_datetime")


def json(obj):
    """Format obj as jsobn string."""
    return _json.dumps(obj, default=str)


def render_bool(val):
    """Render a boolean as checkmark or cross icon."""
    return f"<i class=\"{'green check circle icon' if val else 'red times circle icon'}\"></i>"


def render_datetime(dt):
    """Render a datetime to a standardized format."""
    return dt.strftime(current_app.config["DATETIME_FORMAT"])
