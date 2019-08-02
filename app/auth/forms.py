from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from flask_babel import _, lazy_gettext as _l

from app.models import Topic, User, Subscription


__all__ = (
    "LoginForm",
    "RegistrationForm",
    "ProfileForm",
    "SubscriptionForm",
    "AccessTokenForm",
)


class LoginForm(FlaskForm):
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    remember_me = BooleanField(_l("Remember Me"))
    submit = SubmitField(_l("Login"))


class RegistrationForm(FlaskForm):
    display_name = StringField(_l("Display name"), validators=[DataRequired()])
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    password2 = PasswordField(
        _l("Repeat Password"), validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField(_l("Register"))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_("Please use a different email address."))


class ProfileForm(FlaskForm):
    email = StringField(_l("New Email"), validators=[Email()])
    password = PasswordField(_l("New Password"))
    password2 = PasswordField(_l("New Repeat Password"), validators=[EqualTo("password")])
    topics = QuerySelectMultipleField(_l("Topics"), query_factory=lambda: Topic.query)
    submit = SubmitField(_l("Save"))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None and user.id != current_user.id:
            raise ValidationError(_("Please use a different email address."))


class SubscriptionForm(FlaskForm):
    remind_me = BooleanField(_l("Remind me"))
    mode = SelectField(
        _("Mode"),
        choices=Subscription.Modes.choices(),
        coerce=Subscription.Modes.coerce,
    )
    submit = SubmitField(_l("Save"))


class AccessTokenForm(FlaskForm):
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    submit = SubmitField(_l("Enable"))
