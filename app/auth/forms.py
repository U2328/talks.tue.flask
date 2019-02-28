from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from flask_babel import _, lazy_gettext as _l

from .models import User
from app.core.models import Tag


__all__ = (
    'LoginForm',
    'RegistrationForm',
    'ProfileForm',
)


class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Login'))


class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Register'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different username.'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different email address.'))


class ProfileForm(FlaskForm):
    email = StringField(_l('Email'), validators=[Email()])
    password = PasswordField(_l('Password'))
    password2 = PasswordField(_l('Repeat Password'), validators=[EqualTo('password')])
    tags = QuerySelectMultipleField(_l('Categories'), query_factory=lambda: Tag.query.all())
    submit = SubmitField(_l('Save'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None and user.id != current_user.id:
            raise ValidationError(_('Please use a different email address.'))
