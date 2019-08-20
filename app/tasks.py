import datetime
from itertools import groupby

from flask import render_template

from . import celery, mail
from .models import User, Subscription


def lookup_subscription_type(s):
    return {"daily": Subscription.Modes.DAILY, "weekly": Subscription.Modes.WEEKLY}.get(
        s
    )


@celery.task()
def send_subscription_emails(target_name):
    target = lookup_subscription_type(target_name)
    if target is None:
        raise ValueError("Unknown subscription mode identifier.")
    try:
        print(f"START EMAIL: <{target.name}>")
        cut_off_date = (
            datetime.datetime.now()
            + datetime.timedelta(days=1 if target_name == "daily" else 7)
        ).date()
        for user in User.query.filter(User.is_verified == True):
            talks = {
                key: sorted(
                    [
                        {
                            "id": talk.id,
                            "time": [talk.start_timestamp, talk.end_timestamp],
                            "title": talk.title,
                            "speaker": talk.speaker_name,
                        }
                        for talk in talks
                    ],
                    key=lambda talk: talk["time"][0],
                )
                for key, talks in groupby(
                    user.upcoming_talks, key=lambda talk: talk.start_timestamp.date()
                )
                if key <= cut_off_date
            }
            print(f">> '{user.email}' {talks}")
            if talks:
                send_mail.delay(
                    recipient=user.email,
                    subject=f"Talks.Tue -- {target_name} reminder",
                    template="messages/reminder.html",
                    context={
                        "user": user.display_name,
                        "talks": talks,
                        "target": target,
                    },
                )
        print(f"DONE: <{target.name}>")
    except Exception as e:
        print(f"!!! {e}")
        raise e


@celery.task()
def send_mail(recipient, subject, template, context, sender=None):
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


@celery.task()
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


@celery.task()
def heart_beat():
    print(f"--- HEART BEAT @ {datetime.datetime.now()} ---")
