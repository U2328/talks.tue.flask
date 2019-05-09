from flask_mail import Message

# from flask import render_template


from . import celery, mail
from .models import User


@celery.task()
def send_subscription_emails(target):
    try:
        print(f"START EMAIL: <{target.name}>")
        for user in User.query.all():
            talks = user.upcoming_talks
            print(f">> '{user.email}' {talks}")
            mail.send_message(
                subject=f"Talks.Tue -- {target} reminder",
                # body=render_template("messages/reminder", user=user, talks=talks)
                body=str(talks),
                sender=("Talks.Tue", "no-reply@talks.tue"),
                recipients=[user.email],
            )
        print(f"DONE: <{target.name}>")
    except Exception as e:
        print(f"!!! {e}")
        raise e


@celery.task(name="heart_beat")
def heart_beat():
    print("--- HEART BEAT ---")
