from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextField, HiddenField, DateTimeField
from wtforms.validators import DataRequired, ValidationError
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField, QuerySelectField
from flask_pagedown.fields import PageDownField

from app.core.models import Tag, Speaker


class TalkForm(FlaskForm):
    id = HiddenField('id')
    name = StringField('Name', validators=[DataRequired()])
    description = PageDownField('Description', validators=[])
    timestamp = DateTimeField("Date/Time", format="%Y.%m.%d %H:%M", validators=[DataRequired()])
    speaker = QuerySelectField('Speaker', query_factory=lambda: Speaker.query.all(), get_pk=lambda s: s.id, validators=[DataRequired()])
    tags = QuerySelectMultipleField('Categories', query_factory=lambda: Tag.query.all())
    password = PasswordField('Password')
    submit = SubmitField('Save')



class SpeakerForm(FlaskForm):
    id = HiddenField('id')
    name = StringField('Name', validators=[DataRequired()])
    familiy_name = StringField('Familiy Name', validators=[DataRequired()])
    about_me = PageDownField('About me', validators=[])
    password = PasswordField('Password')
    submit = SubmitField('Save')
