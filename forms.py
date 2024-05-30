from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp, ValidationError
from flask import session
from models import User, Project, Task
from datetime import datetime

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"placeholder": "Email"})
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use. Please choose a different one.')

class AccountForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()], render_kw={"placeholder": "Enter current password"})
    username = StringField('New Username', render_kw={"placeholder": "Enter new username"})
    email = StringField('New Email', validators=[Email()], render_kw={"placeholder": "Enter new email"})
    new_password = PasswordField('New Password', validators=[Length(min=8, message="Password must be at least 8 characters long"), Regexp('^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&].{7,}$', message="Password must include one lowercase letter, one uppercase letter, one digit, and one special character")], render_kw={"placeholder": "Enter new password"})
    submit_username = SubmitField('Update Username')
    submit_email = SubmitField('Update Email')
    submit_password = SubmitField('Update Password')
    submit_delete_account = SubmitField('Delete Account')

    def validate_current_password(self, field):
        user = User.query.filter_by(username=session['username']).first()
        if not user or not user.check_password(field.data):
            raise ValidationError('Invalid current password.')

class LoginForm(FlaskForm):
    username = StringField('Username/Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class DeleteAccountForm(FlaskForm):
    delete_account_password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Delete Account')

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    deadline = DateTimeField('Deadline', format='%Y-%m-%d %H:%M:%S', default=datetime.utcnow)
    submit = SubmitField('Create Project')

class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    deadline = DateTimeField('Deadline', format='%Y-%m-%d %H:%M:%S', default=datetime.utcnow)
    submit = SubmitField('Add Task')
