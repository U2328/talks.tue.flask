import json

import dill
from sqlalchemy import inspect
from sqlalchemy.types import TypeDecorator, LargeBinary


__all__ = ("Binary", "Json", "DillField")


class Serializer:
    def __init__(self, *args, **kwargs):
        raise RuntimeError(f"{self.__class__.__name__} is namespace!")

    @staticmethod
    def transform(data, model_transform, model_check):
        f = lambda x: Serializer.transform(x, model_transform, model_check)
        if model_check(data):
            return model_transform(data)
        elif isinstance(data, dict):
            return {f(key): f(value) for key, value in data.items()}
        elif isinstance(data, (list, set, tuple)):
            return type(data)(f(value) for value in data)
        else:
            return data

    @staticmethod
    def make_serializable(data):
        from .models import MODEL_REGISTRY

        return Serializer.transform(
            data,
            lambda instance: {
                "__type__": "proxy",
                "model": instance.__class__.__name__,
                "identifier": inspect(instance).identity,
            },
            lambda instance: (type(instance).__name__ in MODEL_REGISTRY),
        )

    @staticmethod
    def make_readable(data):
        from .models import MODEL_REGISTRY

        return Serializer.transform(
            data,
            lambda proxy: MODEL_REGISTRY[proxy["model"]].query.get(
                *proxy["identifier"]
            ),
            lambda proxy: (
                isinstance(proxy, dict)
                and all(
                    key in ["__type__", "model", "identifier"] for key in proxy.keys()
                )
                and proxy.get("__type__") == "proxy"
                and proxy.get("model") in MODEL_REGISTRY
            ),
        )


class Binary(Serializer):
    @staticmethod
    def serialize(data):
        return dill.dumps(Binary.make_serializable(data))

    @staticmethod
    def deserialize(data):
        return Binary.make_readable(dill.loads(data))


class Json(Serializer):
    @staticmethod
    def serialize(data):
        return json.dumps(Json.make_serializable(data))

    @staticmethod
    def deserialize(data):
        return Json.make_readable(json.loads(data))


class DillField(TypeDecorator):
    """
    Allows the storage of almost anything in the DB.
    """

    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = Binary.serialize(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = Binary.deserialize(value)
        return value
