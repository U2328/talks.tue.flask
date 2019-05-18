import json as _json

__all__ = ("json",)


def json(obj):
    """Format obj as jsobn string."""
    return _json.dumps(obj, default=str)
