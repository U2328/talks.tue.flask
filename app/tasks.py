from flask_emails import Message

# from flask import render_template


from . import celery
from .models import User


@celery.task()
def send_subscription_emails(target):
    try:
        print(f"START EMAIL: <{target.name}>")
        for user in User.query.all():
            talks = [talk for talk in user.related_talks]
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


@celery.task(name="heart_beat")
def heart_beat():
    print("--- HEART BEAT ---")
