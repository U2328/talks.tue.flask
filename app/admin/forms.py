from datetime import datetime
from dateutil.parser import parse as parse_datetime

from sqlalchemy import or_
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, DateTimeField as _DateTimeField, TextAreaField
from wtforms.validators import DataRequired, Length
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField, QuerySelectField
from flask_babel import lazy_gettext as _l

from app.models import Tag, Collection, User


__all__ = (
    'TalkForm',
    'CollectionForm',
    'TagForm',
)


class DateTimeField(_DateTimeField):
    def process_formdata(self, valuelist):
        if valuelist:
            date_str = " ".join(valuelist)
            try:
                self.data = parse_datetime(date_str)
            except ValueError:
                self.data = None
                raise ValueError(self.gettext("Not a valid datetime value"))


class CollectionForm(FlaskForm):
    title = StringField(_l('Name'), validators=[DataRequired(), Length(max=64)])
    description = TextAreaField(_l('Description'))
    is_meta = BooleanField(_l('Is meta?'), default=False)
    meta_collections = QuerySelectMultipleField(_l('Meta Collections'), query_factory=lambda: Collection.query.filter(Collection.is_meta == True))
    organizer = QuerySelectField(_l('Organizer'), query_factory=lambda: User.query.filter(or_(User.is_organizer == True, User.is_admin == True)))
    editors = QuerySelectMultipleField(_l('Editors'), query_factory=lambda: User.query)
    submit = SubmitField(_l('Save'))


class TagForm(FlaskForm):
    name = StringField(_l('Name'), validators=[DataRequired(), Length(max=64)])
    submit = SubmitField(_l('Add'))


class TalkForm(FlaskForm):
    title = StringField(_l('Name'), validators=[DataRequired(), Length(max=64)])
    description = TextAreaField(_l('Description'))
    timestamp = DateTimeField(_l('Date/Time'), format="%Y.%m.%d %H:%M", default=datetime.now, validators=[DataRequired()])
    speaker_name = StringField(_l('Speaker\'s Name'), validators=[DataRequired(), Length(max=64)])
    speaker_aboutme = TextAreaField(_l('Speaker\'s About me'))
    collections = QuerySelectMultipleField(_l('Collections'), query_factory=lambda: Collection.query.filter(Collection.is_meta == False))
    tags = QuerySelectMultipleField(_l('Categories'), query_factory=lambda: Tag.query)
    submit = SubmitField(_l('Save'))
