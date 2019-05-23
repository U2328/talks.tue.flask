import json as _json

__all__ = ("json",)


def json(obj):
    """Format obj as jsobn string."""
    return _json.dumps(obj, default=str)


def render_bool(val):
    """Render a boolean as checkmark or cross icon."""
    return f"<i class=\"{'green check circle icon' if val else 'red times circle icon'}\"></i>"
