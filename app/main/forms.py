from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField, MultipleFileField
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import ValidationError
# from flask_pagedown.fields import PageDownField
from flask_wtf.file import FileAllowed, FileRequired, FileField


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')

class UploadForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    # validated = BooleanField('Validated Data')
    comments = TextAreaField("Comments")
    language = SelectField('Languages', choices = [('cpp', 'C++'), ('py', 'Python')])

    data_file = FileField('Data File', validators=[
                                    FileRequired(),
                                    FileAllowed(['xyz', 'png'], 'Only data files formats are allowed!')
                ])

    submit = SubmitField('Upload')
