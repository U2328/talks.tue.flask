from flask import render_template, redirect, flash, url_for, request, abort, current_app
from flask_login import current_user, login_user, logout_user, login_required
from flask_babel import _

from app import db
from app.utils import is_safe_url
from . import bp
from .models import User
from .forms import LoginForm, RegistrationForm, ProfileForm


__all__ = (
    'login',
    'logout',
    'register',
    'profile',
)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'), 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        flash(_('Logged in as %(username)s.', username=user.username), 'info')
        current_app.logger.info(f"User logged in: {user}")
        next = request.args.get('next')
        if not is_safe_url(next):
            return abort(400)
        return redirect(next or url_for('core.index'))
    return render_template('auth/login.html', title='Sign In', form=form)


@bp.route('/logout')
def logout():
    current_app.logger.info(f"User logged out: {current_user}")
    logout_user()
    flash(_('Logged out.'), 'info')
    return redirect(url_for('core.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))
    form = RegistrationForm(request.form)
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now a registered user!'), 'success')
        current_app.logger.info(f"New user registered: {user}")
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user
    form = ProfileForm(request.form, obj=user)
    if form.validate_on_submit():
        if form.password.data is not None:
            user.set_password(form.password.data)
        if form.email is not None:
            user.email = form.email.data
        if form.tags is not None:
            user.tags = form.tags.data
        db.session.commit()
        flash(_('Your profile has been updated.'), 'success')
        current_app.logger.info(f"Updated user: {user}")
        return redirect(url_for('auth.login'))
    return render_template('auth/profile.html', title="Profile", form=form, user=user)
