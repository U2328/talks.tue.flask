from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,\
                    HiddenField, DateTimeField, BooleanField
from wtforms.validators import DataRequired, Length
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField, QuerySelectField
from flask_pagedown.fields import PageDownField
from flask_babel import azy_gettext as _l

from app.core.models import Tag, Speaker


__all__ = (
    'TalkForm',
    'SpeakerForm',
    'TagForm',
)


class TalkForm(FlaskForm):
    id = HiddenField('id')
    name = StringField(_l('Name'), validators=[DataRequired(), Length(max=64)])
    description = PageDownField(_l('Description'))
    timestamp = DateTimeField(_l('Date/Time'), format="%Y.%m.%d %H:%M", default=datetime.now(), validators=[DataRequired()])
    speaker = QuerySelectField(_l('Speaker'), query_factory=lambda: Speaker.query.all(), get_pk=lambda s: s.id, validators=[DataRequired()])
    tags = QuerySelectMultipleField(_l('Categories'), query_factory=lambda: Tag.query.all())
    password = PasswordField(_l('Password'))
    submit = SubmitField(_l('Save'))


class SpeakerForm(FlaskForm):
    id = HiddenField('id')
    name = StringField(_l('Name'), validators=[DataRequired(), Length(max=64)])
    familiy_name = StringField(_l('Familiy Name'), validators=[DataRequired(), Length(max=64)])
    familiy_name_first = BooleanField(_l('Family name first?'))
    about_me = PageDownField(_l('About me'))
    password = PasswordField(_l('Password'))
    submit = SubmitField(_l('Save'))


class TagForm(FlaskForm):
    name = StringField(_l('Name'), validators=[Length(min=1, max=32)])
    submit = SubmitField(_l('Add'))
