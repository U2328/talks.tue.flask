from flask_emails import Message
from flask import render_template


from . import celery
from .models import Subscription, User


def email_job(target):
    try:
        grouped_subscriptions = (
            (
                user,
                Subscription.query.filter(
                    Subscription.mode == target, Subscription.user == user
                ),
            )
            for user in User.query.filter(
                User.subscriptions.any(Subscription.mode == target)
            )
        )
        print(f"START EMAIL: <{target.name}>")
        for user, subscriptions in grouped_subscriptions:
            talks = list(
                set(
                    talk
                    for subscription in subscriptions
                    for talk in subscription.collection.related_talks
                )
            )
            print(f">> '{user.email}' {talks}")
            response = Message(
                subject=f"Talks.Tue -- {target} reminder",
                # html=render_template("messages/reminder", user=user, talks=talks)
                html=str(talks),
                mail_from=("Talks.Tue", "no-reply@talks.tue"),
            ).send(to=user.email)
            print(f">> {response}")
        print(f"DONE: <{target.name}>")
    except Exception as e:
        print(f"!!! {e}")
        raise e


def daily_email():
    email_job(target=Subscription.Modes.DAILY)


def weekly_email():
    email_job(target=Subscription.Modes.WEEKLY)
