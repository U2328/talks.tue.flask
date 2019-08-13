from flask import (
    render_template,
    redirect,
    flash,
    url_for,
    request,
    abort,
    current_app,
    session,
)
from flask_login import current_user, login_user, logout_user, login_required
from flask_babel import gettext as _, lazy_gettext as _l

from app import db
from app.utils import is_safe_url
from app.models import User, Subscription, Collection, Talk, AccessToken
from app.api.routes import TalkTable
from . import bp
from .forms import (
    LoginForm,
    RegistrationForm,
    ProfileForm,
    SubscriptionForm,
    AccessTokenForm,
)


__all__ = (
    "login",
    "logout",
    "register",
    "profile",
    "subscribe",
    "subscription",
    "unsubscribe",
)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("core.index"))
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_("Invalid email or password"), "danger")
            return redirect(url_for("auth.login"))
        login_user(user, remember=form.remember_me.data)
        flash(
            _("Logged in as %(display_name)s.", display_name=user.display_name), "info"
        )
        current_app.logger.info(f"User logged in: {user}")
        next = request.args.get("next")
        if not is_safe_url(next):
            return abort(400)
        return redirect(next or url_for("core.index"))
    return render_template("auth/login.html", title="Sign In", form=form)


@bp.route("/logout")
def logout():
    current_app.logger.info(f"User logged out: {current_user}")
    logout_user()
    flash(_("Logged out."), "info")
    return redirect(url_for("core.index"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("core.index"))
    form = RegistrationForm(request.form)
    if form.validate_on_submit():
        user = User(display_name=form.display_name.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_("Congratulations, you are now a registered user!"), "success")
        current_app.logger.info(f"New user registered: {user}")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", title="Register", form=form)


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user
    form = ProfileForm(request.form, obj=user)
    if form.validate_on_submit():
        if form.password.data:
            user.set_password(form.password.data)
        if form.email is not None:
            user.email = form.email.data
        if form.topics is not None:
            user.topics = form.topics.data
        db.session.commit()
        flash(_("Your profile has been updated."), "success")
        current_app.logger.info(f"Updated user: {user}")
        return redirect(url_for("auth.profile"))
    return render_template(
        "auth/profile.html",
        title="Profile",
        form=form,
        user=user,
        subscriptions=current_user.subscriptions,
    )


@bp.route("/collection/<int:id>/subscribe")
@login_required
def subscribe(id):
    collection = Collection.query.get(id)
    if collection is None:
        return abort(404)

    db.session.add(Subscription(user=current_user, collection=collection))
    db.session.commit()

    next = request.args.get("next")
    return (
        abort(400)
        if not is_safe_url(next)
        else redirect(next or url_for("auth.subscription", id=id))
    )


@bp.route("/collection/<int:id>/subscription", methods=["GET", "POST"])
@login_required
def subscription(id):
    subscription = Subscription.query.filter(
        Subscription.user == current_user, Subscription.collection_id == id
    )
    if not subscription:
        return abort(404)
    else:
        subscription = subscription[0]

    next = request.args.get("next")
    if not is_safe_url(next):
        return abort(400)
    else:
        next = next or url_for("auth.profile")

    form = SubscriptionForm(obj=subscription)
    if form.validate_on_submit():
        form.populate_obj(subscription)
        db.session.commit()
        return redirect(next)
    return render_template(
        "auth/subscription.html",
        title=_l(
            "Subscription to %(collection)s", collection=subscription.collection.title
        ),
        subscription=subscription,
        form=form,
        next=next,
    )


@bp.route("/collection/<int:id>/unsubscribe")
@login_required
def unsubscribe(id):
    subscription = Subscription.query.filter(
        Subscription.collection_id == id, Subscription.user == current_user
    )
    if not subscription:
        return abort(404)
    else:
        subscription = subscription[0]

    next = request.args.get("next")
    if not is_safe_url(next):
        return abort(400)
    else:
        next = next or url_for("auth.profile")

    db.session.delete(subscription)
    db.session.commit()
    return redirect(next)


@bp.route("/subscriptions")
@login_required
def subscriptions():
    table = TalkTable(
        query=Talk.query.filter(
            Talk.id.in_([talk.id for talk in current_user.upcoming_talks])
        )
    )
    return render_template("auth/subscriptions.html", table=table)


# Disabled for now as the related issue has been put on hold.
# @bp.route("/token/<uuid>", methods=["GET", "POST"])
def token_login(uuid):
    form = AccessTokenForm(request.form)
    if form.validate_on_submit():
        token = AccessToken.query.filter_by(uuid=uuid).first()
        if token is None:
            return abort(404)
        if not token.check_password(form.password.data):
            flash(_("Invalid password"), "error")
            return redirect(url_for("auth.token_login", uuid=uuid))
        if "access_tokens" not in session:
            session["access_tokens"] = []
        session["access_tokens"].append(token.id)
        session.modified = True
        flash(_("Enabled access token %(uuid)s.", uuid=uuid), "info")
        next = request.args.get("next")
        if not is_safe_url(next):
            return abort(400)
        return redirect(next or url_for("core.index"))
    return render_template(
        "auth/token_login.html", title="Enable token access", uuid=uuid, form=form
    )
