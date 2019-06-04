from datetime import datetime
from dateutil.parser import parse as parse_datetime

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    BooleanField,
    DateTimeField as _DateTimeField,
    TextAreaField,
    PasswordField,
)


from wtforms.validators import DataRequired, Length, ValidationError, Email, EqualTo
from wtforms_alchemy.fields import QuerySelectMultipleField, QuerySelectField
from flask_babel import lazy_gettext as _l

from app.models import Tag, Collection, User


__all__ = ("TagForm", "TalkForm", "CollectionForm", "UserForm")


class TagForm(FlaskForm):
    name = StringField(_l("Name"), validators=[DataRequired(), Length(max=64)])
    submit = SubmitField(_l("Add"))


class DateTimeField(_DateTimeField):
    def process_formdata(self, valuelist):
        if valuelist:
            date_str = " ".join(valuelist)
            try:
                self.data = parse_datetime(date_str)
            except ValueError:
                self.data = None
                raise ValueError(self.gettext("Not a valid datetime value"))


class TalkForm(FlaskForm):
    title = StringField(_l("Name"), validators=[DataRequired(), Length(max=64)])
    description = TextAreaField(_l("Description"))
    timestamp = DateTimeField(
        _l("Date/Time"),
        format="%Y.%m.%d %H:%M",
        default=datetime.now,
        validators=[DataRequired()],
    )
    speaker_name = StringField(
        _l("Speaker's Name"), validators=[DataRequired(), Length(max=64)]
    )
    speaker_aboutme = TextAreaField(_l("Speaker's Bio"))
    collections = QuerySelectMultipleField(
        _l("Collections"),
        query_factory=lambda: Collection.query.filter(Collection.is_meta == False),
    )
    tags = QuerySelectMultipleField(_l("Categories"), query_factory=lambda: Tag.query)
    submit = SubmitField(_l("Save"))


class CollectionForm(FlaskForm):
    title = StringField(_l("Name"), validators=[DataRequired(), Length(max=64)])
    description = TextAreaField(_l("Description"))
    is_meta = BooleanField(_l("Is meta?"), default=False)
    meta_collections = QuerySelectMultipleField(
        _l("Meta Collections"),
        query_factory=lambda: Collection.query.filter(Collection.is_meta == True),
    )
    organizer = QuerySelectField(
        _l("Organizer"),
        query_factory=lambda: User.query.filter(User.is_organizer == True),
    )
    editors = QuerySelectMultipleField(_l("Editors"), query_factory=lambda: User.query)
    submit = SubmitField(_l("Save"))


class UserForm(FlaskForm):
    username = StringField(_l("Username"), validators=[DataRequired()])
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    is_admin = BooleanField(_l("Is Admin?"))
    is_organizer = BooleanField(_l("Is Organizer?"))
    submit = SubmitField(_l("Save"))

    def validate_username(self, username):
        if username.data != username.object_data:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError(_l("Please use a different username."))

    def validate_email(self, email):
        if email.data != email.object_data:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError(_l("Please use a different email address."))


class AccessTokenForm(FlaskForm):
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    password2 = PasswordField(
        _l("Repeat Password"), validators=[DataRequired(), EqualTo("password")]
    )
