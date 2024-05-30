from app_init import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import validates
import pytz


# Association table for many-to-many relationship between Project and User
project_participants = db.Table('project_participants',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    extend_existing=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    projects = db.relationship('Project', secondary=project_participants, backref=db.backref('participants_projects', lazy='dynamic'), overlaps="participated_projects,projects")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = db.relationship('User', backref=db.backref('owned_projects', lazy=True))
    participants = db.relationship('User', secondary=project_participants, backref=db.backref('participated_projects', lazy='dynamic'), lazy='dynamic', overlaps="participants_projects,projects")
    start_date = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Europe/Istanbul')))
    deadline = db.Column(db.DateTime, nullable=True)

    @validates('deadline')
    def validate_deadline(self, key, deadline):
        if deadline and self.deadline and deadline > self.deadline:
            raise ValueError("Task deadline cannot exceed project deadline.")
        return deadline


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    project = db.relationship('Project', backref=db.backref('tasks', lazy=True))
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    assignee = db.relationship('User', backref=db.backref('tasks', lazy=True))
    completed = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Free')
    start_date = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Europe/Istanbul')))
    deadline = db.Column(db.DateTime, nullable=True)

class ProjectComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Europe/Istanbul')), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('project.comments', lazy=True))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    project = db.relationship('Project', backref=db.backref('project.comments', lazy=True))

    def __repr__(self):
        return f"Comment('{self.content}', '{self.date_posted}')"


class TaskComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Europe/Istanbul')), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('task.comments', lazy=True))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    task = db.relationship('Task', backref=db.backref('task.comments', lazy=True))

    def __repr__(self):
        return f"Comment('{self.content}', '{self.date_posted}')"
    