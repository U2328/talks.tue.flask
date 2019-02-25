from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateTimeField, SubmitField, TextField
from wtforms.validators import DataRequired, ValidationError
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField, QuerySelectField
from flask_pagedown.fields import PageDownField

from app.core.models import Tag, Speaker


class TalkForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = PageDownField('Description', validators=[])
    timestamp = DateTimeField("Date/Time", format="%Y-%m-%dT%H:%M:%S", default=datetime.now(), validators=[DataRequired()])
    speaker = QuerySelectField('Speaker', query_factory=lambda: Speaker.query.all(), validators=[DataRequired()])
    tags = QuerySelectMultipleField('Categories', query_factory=lambda: Tag.query.all())
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Save')



class SpeakerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    familiy_name = StringField('Familiy Name', validators=[DataRequired()])
    about_me = PageDownField('About me', validators=[])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Save')
