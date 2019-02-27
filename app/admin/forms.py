from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextField, HiddenField, DateTimeField, BooleanField
from wtforms.validators import DataRequired, ValidationError, Length
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField, QuerySelectField
from flask_pagedown.fields import PageDownField
from flask_babel import _

from app.core.models import Tag, Speaker


class TalkForm(FlaskForm):
    id = HiddenField('id')
    name = StringField(_('Name'), validators=[DataRequired(), Length(max=64)])
    description = PageDownField(_('Description'))
    timestamp = DateTimeField(_('Date/Time'), format="%Y.%m.%d %H:%M", validators=[DataRequired()])
    speaker = QuerySelectField(_('Speaker'), query_factory=lambda: Speaker.query.all(), get_pk=lambda s: s.id, validators=[DataRequired()])
    tags = QuerySelectMultipleField(_('Categories'), query_factory=lambda: Tag.query.all())
    password = PasswordField(_('Password'))
    submit = SubmitField(_('Save'))



class SpeakerForm(FlaskForm):
    id = HiddenField('id')
    name = StringField(_('Name'), validators=[DataRequired(), Length(max=64)])
    familiy_name = StringField(_('Familiy Name'), validators=[DataRequired(), Length(max=64)])
    familiy_name_first = BooleanField(_('Family name first?'))
    about_me = PageDownField(_('About me'))
    password = PasswordField(_('Password'))
    submit = SubmitField(_('Save'))


class TagForm(FlaskForm):
    name = StringField(_('Name'), validators=[Length(min=1, max=32)])
    submit = SubmitField(_('Add'))
