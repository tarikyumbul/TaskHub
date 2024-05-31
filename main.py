from app_init import app, db
from models import User, Project, Task, ProjectComment, TaskComment
from forms import LoginForm, RegistrationForm, AccountForm, DeleteAccountForm
from flask import session, render_template, request, redirect, url_for, flash
from datetime import datetime

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

# Ensure the database tables are created
with app.app_context():
    db.create_all()
    if not hasattr(Task, 'completed'):
        with db.engine.connect() as conn:
            conn.execute('ALTER TABLE task ADD COLUMN completed BOOLEAN DEFAULT FALSE')

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

@app.route("/projects", methods=['GET', 'POST'])
def projects():
    if 'username' not in session:
        flash('You must be logged in to view this page.')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    if user is None:
        flash('User not found.')
        return redirect(url_for('logout'))
    if request.method == 'POST':
        project_name = request.form.get('project_name')
        project_description = request.form.get('project_description')
        project_deadline_str = request.form.get('project_deadline')
        start_date = datetime.now()
        if project_name and project_description and user and start_date and project_deadline_str:
            project_deadline = datetime.strptime(project_deadline_str, '%Y-%m-%dT%H:%M')
            new_project = Project(name=project_name, description=project_description, owner=user, start_date=start_date, deadline=project_deadline)  # Include start date and deadline in project creation
            new_project.participants.append(user)
            new_project.owner_id = user.id
            db.session.add(new_project)
            db.session.commit()
            flash('Project created successfully!')
            return redirect(url_for('projects'))
    projects = user.participated_projects.all()
    return render_template('projects.html', projects=projects, user=user)

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

@app.route("/project/<int:project_id>", methods=['GET', 'POST'])
def project(project_id):
    if 'username' not in session:
        flash('You must be logged in to view this page.')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    if user is None:
        flash('User not found.')
        return redirect(url_for('logout'))
    
    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        if 'task_title' in request.form:
            task_title = request.form.get('task_title')
            task_description = request.form.get('task_description')
            task_deadline_str = request.form.get('task_deadline')
            task_deadline = datetime.strptime(task_deadline_str, '%Y-%m-%dT%H:%M')
            new_task = Task(title=task_title, description=task_description, deadline=task_deadline, project=project)
            db.session.add(new_task)
            db.session.commit()
            flash('Task added successfully!')
            return redirect(url_for('project', project_id=project_id))
        elif 'participant_username' in request.form:
            participant_username = request.form.get('participant_username')
            participant = User.query.filter_by(username=participant_username).first()
            if participant:
                if participant not in project.participants:
                    project.participants.append(participant)
                    db.session.commit()
                    flash('Participant added successfully!')
                else:
                    flash('Participant is already associated with the project.')
            else:
                flash('Invalid username. Please try again.')
            return redirect(url_for('project', project_id=project_id))
        elif 'remove_participant_id' in request.form:
            participant_id = request.form.get('remove_participant_id')
            participant = User.query.get(participant_id)
            if participant and participant in project.participants:
                project.participants.remove(participant)
                db.session.commit()
                flash('Participant removed successfully!')
            else:
                flash('Participant not found in the project.')
            return redirect(url_for('project', project_id=project_id))
        elif 'comment_content' in request.form:
            comment_content = request.form.get('comment_content')
            new_comment = ProjectComment(content=comment_content, user=user, project=project)
            db.session.add(new_comment)
            db.session.commit()
            flash('Comment added successfully!')
            return redirect(url_for('project', project_id=project_id))
    
    comments = ProjectComment.query.filter_by(project_id=project_id).order_by(ProjectComment.date_posted.desc()).all()
    now = datetime.now()
    participants = project.participants.all()
    return render_template('project.html', project=project, user=user, tasks=project.tasks, comments=comments, now=now, participants=participants)

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

@app.route("/delete_project_comment/<int:comment_id>", methods=['POST'])
def delete_project_comment(comment_id):
    comment = ProjectComment.query.get_or_404(comment_id)
    if 'username' not in session or comment.user.username != session['username']:
        flash('You do not have permission to delete this comment.')
        return redirect(url_for('home_route'))
    
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted successfully!')
    
    if comment.project_id:
        return redirect(url_for('project', project_id=comment.project_id))

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

@app.route("/delete_task_comment/<int:comment_id>", methods=['POST'])
def delete_task_comment(comment_id):
    comment = TaskComment.query.get_or_404(comment_id)
    if 'username' not in session or comment.user.username != session['username']:
        flash('You do not have permission to delete this comment.')
        return redirect(url_for('home_route'))
    
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted successfully!')

    if comment.task_id:
        return redirect(url_for('task', task_id=comment.task_id))
    return redirect(url_for('home_route'))

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

@app.route("/task/<int:task_id>", methods=['GET', 'POST'])
def task(task_id):
    task = Task.query.get_or_404(task_id)
    user = User.query.filter_by(username=session['username']).first()
    
    if request.method == 'POST':
        if 'comment_content' in request.form:
            comment_content = request.form.get('comment_content')
            new_comment = TaskComment(content=comment_content, user=user, task=task)
            db.session.add(new_comment)
            db.session.commit()
            flash('Comment added successfully!')
        status = request.form.get('status')
        if status:
            task.status = status
            task.completed = (status == 'Completed')
            db.session.commit()
        assignee_username = request.form.get('assignee_username[]')
        if assignee_username:
            assignee = User.query.filter_by(username=assignee_username).first()
            if assignee:
                if assignee in task.project.participants:
                    task.assignee = assignee
                    db.session.commit()
                    flash('Assignee added successfully!')
                else:
                    flash('Assignee does not have access to the project.')
            else:
                flash('Invalid username for assignee. Please try again.')
        remove_assignee = request.form.get('remove_assignee')
        if remove_assignee:
            if task.assignee:
                task.assignee = None
                db.session.commit()
                flash('Assignee removed successfully!')
            else:
                flash('No assignee to remove.')

        return redirect(url_for('task', task_id=task.id))

    comments = TaskComment.query.filter_by(task_id=task_id).order_by(TaskComment.date_posted.desc()).all()
    return render_template('task.html', task=task, comments=comments)

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

@app.route("/account", methods=['GET', 'POST'])
def account():
    if 'username' not in session:
        flash('You must be logged in to view this page.')
        return redirect(url_for('login'))

    form = AccountForm()
    user = User.query.filter_by(username=session['username']).first()
    if user is None:
        flash('User not found.')
        return redirect(url_for('logout'))

    if form.validate_on_submit():
        if user.check_password(form.current_password.data):
            if form.username.data:
                user.username = form.username.data
            if form.email.data:
                user.email = form.email.data
            if form.new_password.data:
                user.set_password(form.new_password.data)
            if form.submit_delete_account.data:
                db.session.delete(user)
                session.pop('username', None)
                flash('Your account has been deleted.')
                return redirect(url_for('home_route'))
            db.session.commit()
            flash('Account information updated successfully.')
            return redirect(url_for('account'))
        else:
            flash('Invalid current password. Please try again.')

    return render_template('account.html', title='Account Settings', form=form, user=user)

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

@app.route("/update_username", methods=['POST'])
def update_username():
    if 'username' not in session:
        flash('You must be logged in to perform this action.')
        return redirect(url_for('login'))
    form = AccountForm()
    user = User.query.filter_by(username=session['username']).first()
    if user is None:
        flash('User not found.')
        return redirect(url_for('logout'))
    if form.validate_on_submit():
        user.username = form.username.data
        db.session.commit()
        flash('Username updated successfully!')
    else:
        flash('Invalid username. Please try again.')
    return redirect(url_for('account'))

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

@app.route("/update_email", methods=['POST'])
def update_email():
    if 'username' not in session:
        flash('You must be logged in to perform this action.')
        return redirect(url_for('login'))

    form = AccountForm()
    user = User.query.filter_by(username=session['username']).first()
    if user is None:
        flash('User not found.')
        return redirect(url_for('logout'))

    if form.validate_on_submit():
        if user.check_password(form.current_password.data):
            user.email = form.email.data
            db.session.commit()
            flash('Email updated successfully.')
            return redirect(url_for('account'))
        else:
            flash('Invalid current password. Please try again.')

    return redirect(url_for('account'))

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

@app.route("/update_password", methods=['POST'])
def update_password():
    if 'username' not in session:
        flash('You must be logged in to perform this action.')
        return redirect(url_for('login'))

    form = AccountForm()
    user = User.query.filter_by(username=session['username']).first()
    if user is None:
        flash('User not found.')
        return redirect(url_for('logout'))

    if form.validate_on_submit():
        if user.check_password(form.current_password.data):
            user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password updated successfully.')
            return redirect(url_for('account'))
        else:
            flash('Invalid current password. Please try again.')

    return redirect(url_for('account'))

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

@app.route("/delete_account", methods=['POST'])
def delete_account():
    if 'username' not in session:
        flash('You must be logged in to perform this action.')
        return redirect(url_for('login'))
    form = DeleteAccountForm()
    user = User.query.filter_by(username=session['username']).first()
    if user is None:
        flash('User not found.')
        return redirect(url_for('logout'))
    if form.validate_on_submit():
        if user and user.check_password(form.delete_account_password.data):
            db.session.delete(user)
            db.session.commit()
            session.pop('username', None)
            flash('Your account has been deleted.')
            return redirect(url_for('home_route'))
        else:
            flash('Invalid password. Please try again.')
    return redirect(url_for('account'))

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter((User.username == form.username.data) | (User.email == form.username.data)).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return render_template('login.html', title='Sign In', form=form, error='Invalid username or password')
        session['username'] = user.username
        flash('You have been logged in!')
        return redirect(url_for('home_route'))
    return render_template('login.html', title='Sign In', form=form)

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

@app.route("/logout")
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('home_route'))

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

@app.route("/")
def home_route():
    return render_template("home.html")

#/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

if __name__ == "__main__":
    from wsgi import initialize
    initialize()
