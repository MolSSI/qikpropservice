from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField, MultipleFileField, IntegerField
from wtforms.fields.html5 import IntegerRangeField
from wtforms.validators import DataRequired, Length, Email, Regexp, NumberRange, Optional
from wtforms import ValidationError
# from flask_pagedown.fields import PageDownField
from flask_wtf.file import FileAllowed, FileRequired, FileField


class ProgramForm(FlaskForm):
    input_file = FileField("Input File", validators=[
        FileRequired(),
        FileAllowed(['mae', 'maegz', 'mae.gz',  # Maestro Files
                     'mol', 'molgz', 'sd', 'sd.gz', 'sdgz', 'sdf', 'sdf.gz', 'sdfgz',  # MDL Files
                     'mol2',  # Mol2 files
                     'pdb',  # PDB files
                     'z'  # BOSS/MCPRO Z-matrix Files
                     ], "Only Maestro, MDL, Mol2, PDB, or BOSS/MCPRO Z-matrix Files are allowed")
    ])
    fast = BooleanField(label="Fast Processing Mode")
    similar = IntegerField(label="Generate this number of most similar molecules relative to last processed",
                           default=20,
                           validators=[Optional(), NumberRange(min=0)])

    # Stuff below here not really implemented
    neutralize = BooleanField(label="Neutralize molecules [-neut] (Maestro-formats only)", default="checked")
    nosa = BooleanField(label="Don't generate the QPSA file with additional data [-nosa], will not be in returned "
                              "tarball")
    sim = BooleanField(label="Generate list of known drugs most similar to each processed molecule [-sim]")
    nsim = IntegerField(label="Generate this number of most similar drug molecules relative to last processed "
                              "[-nsim] incompatible with [-sim]",
                        validators=[Optional()])
    # molecule_bounds = StringField(label="Process the specified range of molecules from the input file. [-n lo:hi]")
    molecule_lower_bound = IntegerField(label="lo:",
                                        validators=[Optional(), NumberRange(min=0)])
    molecule_upper_bound = IntegerField(label="hi:",
                                        validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Run!')

    @classmethod
    def program_kwargs_map(cls):
        """
        Helper function to get the implemented keyword arguments for the form and their map to the QPlimits skeleton
        """
        return {"fast": ""}


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class UploadForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    # validated = BooleanField('Validated Data')
    comments = TextAreaField("Comments")
    language = SelectField('Languages', choices=[('cpp', 'C++'), ('py', 'Python')])

    data_file = FileField('Data File', validators=[
                                    FileRequired(),
                                    FileAllowed(['xyz', 'png'], 'Only data files formats are allowed!')
                ])

    submit = SubmitField('Upload')
