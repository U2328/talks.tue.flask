import json as _json
from flask import current_app

__all__ = ("json", "render_bool", "render_datetime", "length")


def json(obj):
    """Format obj as json string."""
    return _json.dumps(obj, default=str)


def length(obj):
    """Template filter wrapper for len"""
    return len(obj)


def render_bool(val):
    """Render a boolean as checkmark or cross icon."""
    return f"<i class=\"fas {'fa-check-circle text-success' if val else 'fa-times-circle text-danger'}\"></i>"


def render_datetime(dt, default=None):
    """Render a datetime to a standardized format."""
    return (
        dt.strftime(current_app.config["DATETIME_FORMAT"])
        if dt is not None
        else (default or "-")
    )
