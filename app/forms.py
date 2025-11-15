from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class SignupForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField("Repeat Password", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Sign up")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class ClassForm(FlaskForm):
    name = StringField("Class name", validators=[DataRequired()])
    submit = SubmitField("Save")

class StudentForm(FlaskForm):
    name = StringField("Student name", validators=[DataRequired()])
    roll_no = StringField("Roll No")
    class_id = SelectField("Class", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Add Student")

class MarkAttendanceForm(FlaskForm):
    date = DateField("Date", format='%Y-%m-%d')
    # we will dynamically create checkboxes in template
    submit = SubmitField("Save")
