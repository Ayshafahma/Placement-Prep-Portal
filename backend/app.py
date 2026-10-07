from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import os

app = Flask(__name__, template_folder='../frontend/templates')
app.config['SECRET_KEY'] = 'placement_portal_secret_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

SUBJECT_TOPICS = {
    'Data Structures': ['Arrays', 'Linked Lists', 'Stack', 'Queue', 'Trees', 'Graphs'],
    'Algorithms': ['Sorting', 'Binary Search', 'Dynamic Programming', 'Greedy'],
    'Operating Systems': ['Process Management', 'Memory Management', 'File Systems'],
    'DBMS': ['Normalization', 'SQL', 'Primary Key', 'Foreign Key', 'ACID Properties'],
    'Computer Networks': ['OSI Model', 'TCP/IP', 'HTTP', 'DNS', 'Routing'],
    'OOP Concepts': ['Classes', 'Inheritance', 'Polymorphism', 'Abstraction', 'Method Overloading'],
}

# ─── Models ───────────────────────────────────────────────────────────────────

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    # role = db.Column(db.String(10), default='student')  # 'student' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subjects = db.relationship('Subject', backref='user', lazy=True, cascade='all, delete-orphan')
    # questions = db.relationship('Question', backref='user', lazy=True, cascade='all, delete-orphan')

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    total_topics = db.Column(db.Integer, default=0)
    completed_topics = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='not_started')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    topics = db.relationship('Topic', backref='subject', lazy=True, cascade='all, delete-orphan')

# class Question(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     question_text = db.Column(db.Text, nullable=False)
#     answer = db.Column(db.Text, default='')
#     category = db.Column(db.String(50), nullable=False)
#     company = db.Column(db.String(100), default='General')
#     difficulty = db.Column(db.String(20), default='Medium')
#     is_solved = db.Column(db.Boolean, default=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    questions = db.relationship('TopicQuestion', backref='topic', lazy=True, cascade='all, delete-orphan')

class TopicQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, default='')
    difficulty = db.Column(db.String(20), default='Medium')
    is_solved = db.Column(db.Boolean, default=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─── Auth Routes ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('Username taken.', 'danger')
            return render_template('register.html')
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        # defaults = [
        #     ('Data Structures', 'DSA', 10), ('Algorithms', 'DSA', 12),
        #     ('Operating Systems', 'CS Core', 8), ('DBMS', 'CS Core', 10),
        #     ('Computer Networks', 'CS Core', 9), ('OOP Concepts', 'Programming', 6),
        # ]
        defaults = [
    ('Data Structures', 'DSA'),
    ('Algorithms', 'DSA'),
    ('Operating Systems', 'CS Core'),
    ('DBMS', 'CS Core'),
    ('Computer Networks', 'CS Core'),
    ('OOP Concepts', 'Programming'),
]
        for name, cat in defaults:
            topic_list = SUBJECT_TOPICS.get(name, [])
            subject = Subject(name=name, category=cat, total_topics=len(topic_list), user_id=user.id)
            db.session.add(subject)
            db.session.commit()
            for topic_name in topic_list:
                topic = Topic(name=topic_name, subject_id=subject.id)
                db.session.add(topic)
        db.session.commit()
        
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    # questions = Question.query.filter_by(user_id=current_user.id).all()

    total_subjects = len(subjects)
    completed_subjects = sum(1 for s in subjects if s.status == 'completed')
    in_progress = sum(1 for s in subjects if s.status == 'in_progress')

    # total_q = len(questions)
    # solved_q = sum(1 for q in questions if q.is_solved)
    # questions = Question.query.filter_by(user_id=current_user.id).all()

    overall_progress = 0
    if subjects:
        total_t = sum(s.total_topics for s in subjects)
        done_t = sum(s.completed_topics for s in subjects)
        overall_progress = int((done_t / total_t * 100) if total_t > 0 else 0)

    recent_subjects = sorted(subjects, key=lambda x: x.updated_at, reverse=True)[:5]

    return render_template('dashboard.html',
        subjects=subjects,
        total_subjects=total_subjects,
        completed_subjects=completed_subjects,
        in_progress=in_progress,
        # total_q=total_q,
        # solved_q=solved_q,
        overall_progress=overall_progress,
        recent_subjects=recent_subjects
    )

# ─── Subject Management ───────────────────────────────────────────────────────

@app.route('/subjects')
@login_required
def subjects():
    category = request.args.get('category', 'all')
    q = Subject.query.filter_by(user_id=current_user.id)
    if category != 'all':
        q = q.filter_by(category=category)
    subjects = q.order_by(Subject.name).all()
    categories = db.session.query(Subject.category).filter_by(user_id=current_user.id).distinct().all()
    categories = [c[0] for c in categories]
    return render_template('subjects.html', subjects=subjects, categories=categories, selected=category)
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Access denied. Admins only.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

@app.route('/subjects/add', methods=['POST'])
@login_required
@admin_required 
def add_subject():
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    total = int(request.form.get('total_topics', 1) or 1)
    notes = request.form.get('notes', '').strip()
    if name and category:
        s = Subject(name=name, category=category, total_topics=total, notes=notes, user_id=current_user.id)
        db.session.add(s)
        db.session.commit()
        flash(f'Subject "{name}" added!', 'success')
    return redirect(url_for('subjects'))

@app.route('/subjects/update/<int:subject_id>', methods=['POST'])
@login_required
def update_subject(subject_id):
    s = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    s.completed_topics = int(request.form.get('completed_topics', s.completed_topics))
    s.notes = request.form.get('notes', s.notes)
    s.total_topics = int(request.form.get('total_topics', s.total_topics))
    if s.completed_topics >= s.total_topics:
        s.status = 'completed'
    elif s.completed_topics > 0:
        s.status = 'in_progress'
    else:
        s.status = 'not_started'
    s.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Subject updated!', 'success')
    return redirect(url_for('subjects'))

@app.route('/subjects/delete/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    s = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    db.session.delete(s)
    db.session.commit()
    flash('Subject deleted.', 'info')
    return redirect(url_for('subjects'))




    # ─── Topic Routes ─────────────────────────────────────────────────────────────

@app.route('/subjects/<int:subject_id>/topics')
@login_required
def topics(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    topics = Topic.query.filter_by(subject_id=subject_id).all()
    return render_template('topics.html', subject=subject, topics=topics)

@app.route('/topics/toggle/<int:topic_id>', methods=['POST'])
@login_required
def toggle_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    subject = Subject.query.get(topic.subject_id)
    topic.is_completed = not topic.is_completed
    db.session.commit()
    subject.completed_topics = Topic.query.filter_by(subject_id=subject.id, is_completed=True).count()
    if subject.completed_topics >= subject.total_topics:
        subject.status = 'completed'
    elif subject.completed_topics > 0:
        subject.status = 'in_progress'
    else:
        subject.status = 'not_started'
    subject.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('topics', subject_id=subject.id))

# ─── Topic Question Routes ────────────────────────────────────────────────────

@app.route('/topics/<int:topic_id>/questions')
@login_required
def topic_questions(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    subject = Subject.query.filter_by(id=topic.subject_id, user_id=current_user.id).first_or_404()
    questions = TopicQuestion.query.filter_by(topic_id=topic_id).order_by(TopicQuestion.created_at.desc()).all()
    return render_template('topic_questions.html', topic=topic, subject=subject, questions=questions)

@app.route('/topics/<int:topic_id>/questions/add', methods=['POST'])
@login_required
def add_topic_question(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    text = request.form.get('question_text', '').strip()
    answer = request.form.get('answer', '').strip()
    difficulty = request.form.get('difficulty', 'Medium')
    if text:
        q = TopicQuestion(question_text=text, answer=answer, difficulty=difficulty, topic_id=topic_id)
        db.session.add(q)
        db.session.commit()
        flash('Question added!', 'success')
    return redirect(url_for('topic_questions', topic_id=topic_id))

@app.route('/topics/questions/toggle/<int:qid>', methods=['POST'])
@login_required
def toggle_topic_question(qid):
    q = TopicQuestion.query.get_or_404(qid)
    q.is_solved = not q.is_solved
    db.session.commit()
    return redirect(url_for('topic_questions', topic_id=q.topic_id))

@app.route('/topics/questions/delete/<int:qid>', methods=['POST'])
@login_required
def delete_topic_question(qid):
    q = TopicQuestion.query.get_or_404(qid)
    topic_id = q.topic_id
    db.session.delete(q)
    db.session.commit()
    flash('Question deleted.', 'info')
    return redirect(url_for('topic_questions', topic_id=topic_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)