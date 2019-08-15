from urllib.parse import urlparse, urljoin
from typing import Any, NamedTuple, Type, Union, List, Dict, Optional

import dill
from flask import request, render_template
from sqlalchemy import inspect
from sqlalchemy.types import TypeDecorator, LargeBinary


from app import db, cache, mail


__all__ = (
    "is_safe_url",
    "copy_row",
    "DillField",
    "ModelProxy",
    "send_mail",
    "send_mails",
)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def copy_row(row, ignored_columns=[]):
    copy = type(row)()
    for col in row.__table__.columns:
        if col.name not in ignored_columns:
            setattr(copy, col.name, getattr(row, col.name))
    return copy


class ModelProxy(NamedTuple):
    """
    A simple class to easily store and retrieve model instances.
    """

    model: Type[db.Model]
    identifier: Any

    @classmethod
    def from_instance(cls, instance):
        inspection = inspect(instance)
        return cls(instance.__class__, inspection.identity)

    @property
    def instance(self):
        return ModelProxy.retrieve_instance(*self)

    @staticmethod
    @cache.memoize()
    def retrieve_instance(model, identifier):
        return model.query.get(*identifier)


class DillField(TypeDecorator):
    """
    Allows the storage of almost anything in the DB.
    """

    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = dill.dumps(DillField.make_serializable(value))
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = DillField.make_readable(dill.loads(value))
        return value

    @staticmethod
    def make_serializable(data):
        f = DillField.make_serializable
        if isinstance(data, db.Model):
            return ModelProxy.from_instance(data)
        elif isinstance(data, dict):
            return {f(key): f(value) for key, value in data.items()}
        elif isinstance(data, (list, set, tuple)):
            return type(data)(f(value) for value in data)
        else:
            return data

    @staticmethod
    def make_readable(data):
        f = DillField.make_readable
        if isinstance(data, ModelProxy):
            return data.instance
        elif isinstance(data, dict):
            return {f(key): f(value) for key, value in data.items()}
        elif isinstance(data, (list, set, tuple)):
            return type(data)(f(value) for value in data)
        else:
            return data


def send_mail(
    recipient: Union[str, List[str]],
    subject: str,
    template: str,
    context: Dict[str, Any],
    sender: Optional[str] = None,
):
    """Send a single mail

    :param recipient: recipient/s that are to receive the mail
    :param subject: subject to head the mail
    :param template: template to render
    :param context: context to render the template with
    :param sender: sender of the mail, defaults to config.DEFAULT_MAIL_SENDER
    """
    mail.send_message(
        subject=subject,
        recipients=recipient if isinstance(recipient, list) else [recipient],
        html=render_template(template, **context),
        sender=sender,
    )


def send_mails(recipients, subject, template, context, sender=None):
    for recipient in recipients:
        send_mail(
            recipient,
            subject(recipient) if callable(recipient) else subject,
            template,
            {
                key: value(recipient) if callable(value) else value
                for key, value in context.items()
            },
        )
