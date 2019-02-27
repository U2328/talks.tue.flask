from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from flask_babel import _

from .models import User
from app.core.models import Tag


class LoginForm(FlaskForm):
    username = StringField(_('Username'), validators=[DataRequired()])
    password = PasswordField(_('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_('Remember Me'))
    submit = SubmitField(_('Login'))



class RegistrationForm(FlaskForm):
    username = StringField(_('Username'), validators=[DataRequired()])
    email = StringField(_('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_('Password'), validators=[DataRequired()])
    password2 = PasswordField(_('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_('Register'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different username.'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different email address.'))



class ProfileForm(FlaskForm):
    email = StringField(_('Email'), validators=[Email()])
    password = PasswordField(_('Password'))
    password2 = PasswordField(_('Repeat Password'), validators=[EqualTo('password')])
    tags = QuerySelectMultipleField(_('Categories'), query_factory=lambda: Tag.query.all())
    submit = SubmitField(_('Save'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None and user.id != current_user.id:
            raise ValidationError(_('Please use a different email address.'))
