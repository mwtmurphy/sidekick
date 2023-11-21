'''form for creating warm-ups'''

import flask_wtf
import flask_wtf.file as wtfile
import io
import pandas as pd
from werkzeug import utils
import wtforms
from wtforms import validators

from sidekik.models import MoveType, Workout


#admin forms
class LoginForm(flask_wtf.FlaskForm):
    email = wtforms.StringField("Email Address", validators=[validators.DataRequired()])
    password = wtforms.PasswordField("Password", validators=[validators.DataRequired()])
    remember_me = wtforms.BooleanField("Remember Me")
    submit = wtforms.SubmitField("Sign In")


class UploadMoveCatForm(flask_wtf.FlaskForm):
    fmoves = wtforms.FileField(validators=[
        wtfile.FileRequired(), wtfile.FileAllowed(["csv"], "The file provided is not a CSV file.")
    ])
    submit = wtforms.SubmitField("Upload File")
    df = None

    def validate_fmoves(self, fmoves):
        sec_fname = utils.secure_filename(fmoves.data.filename)
        stream = io.StringIO(fmoves.data.read().decode("ascii"), newline=None)
        df = pd.read_csv(stream)

        if list(df.columns) != ["Movement"] + sorted([row.name for row in MoveType.query.all()]):
            raise validators.ValidationError(("The file provided is invalid. The top row must match"
                                                  " the template file"))

        if df["Movement"].duplicated().sum():
            raise validators.ValidationError("The file provided has duplicate movements in it.")

        self.df = df


class UploadMovesForm(flask_wtf.FlaskForm):
    fmoves = wtforms.FileField(validators=[
        wtfile.FileRequired(), wtfile.FileAllowed(["csv"], "The file provided is not a CSV file.")
    ])
    submit = wtforms.SubmitField("Upload File")
    df = None

    def validate_fmoves(self, fmoves):
        sec_fname = utils.secure_filename(fmoves.data.filename)
        stream = io.StringIO(fmoves.data.read().decode("ascii"), newline=None)
        df = pd.read_csv(stream)

        for ix, lab in enumerate(df.columns):
            if lab == f"Unnamed: {ix}":
                raise validators.ValidationError(("The file provided is invalid. The top row cannot"
                                                  " have any empty cells."))
        
        self.df = df


#app forms
class MoveForm(flask_wtf.FlaskForm):
    '''Form for each movement in MoveListForm'''
    move = wtforms.StringField(validators=[validators.Length(max=50)])

    def validate_move(self, move):
        move = move.data.title().strip()
        if move and not Workout.query.filter_by(name=move).first():
            raise validators.ValidationError("Movement not found in workout library.")


class MoveListForm(flask_wtf.FlaskForm):
    '''Form for users to enter movements into'''
    moves = wtforms.FieldList(wtforms.FormField(MoveForm), min_entries=5)
    submit = wtforms.SubmitField("Create Warm-up")

