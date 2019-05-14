import datetime
from itertools import groupby

from flask import render_template
from flask_mail import Message


from . import celery, mail
from .models import User


@celery.task()
def send_subscription_emails(target):
    try:
        print(f"START EMAIL: <{target.name}>")
        for user in User.query.all():
            talks = user.upcoming_talks
            grouped_talks = groupby(talks, key=lambda talk: talk.timestamp.date())
            print(f">> '{user.email}' {talks}")
            print(
                render_template(
                    "messages/reminder.jinja2",
                    user=user,
                    grouped_talks=grouped_talks,
                    target=target,
                )
            )
            """
            message = Message(
                subject=f"Talks.Tue -- {target} reminder",
                # body=render_template("messages/reminder", user=user, grouped_talks=grouped_talks, target=target)
                body=str(grouped_talks),
                sender=("Talks.Tue", "no-reply@talks.tue"),
                recipients=[user.email],
            )
            send_mail.delay(message)
            """
        print(f"DONE: <{target.name}>")
    except Exception as e:
        print(f"!!! {e}")
        raise e


@celery.task()
def send_mail(message):
    mail.send(message)


@celery.task(name="heart_beat")
def heart_beat():
    print(f"--- HEART BEAT @ {datetime.datetime.now()} ---")
