from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json

# Initialize Flask app
app = Flask(__name__)

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'Fest_Management.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize extensions
db = SQLAlchemy(app)

# Initialize login manager after db
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    registrations = db.relationship('EventRegistration', backref='participant', lazy=True)
    quiz_attempts = db.relationship('QuizAttempt', backref='participant', lazy=True)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer)
    registrations = db.relationship('EventRegistration', backref='event', lazy=True)

class EventRegistration(db.Model):
    __tablename__ = 'event_registrations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    questions = db.relationship('Question', backref='quiz', lazy=True)
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy=True)

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text)
    correct_answer = db.Column(db.String(100), nullable=False)

    def get_options(self):
        return json.loads(self.options) if self.options else []

    def set_options(self, options_list):
        self.options = json.dumps(options_list)

class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    attempt_date = db.Column(db.DateTime, default=datetime.utcnow)

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    priority = db.Column(db.String(20), default='normal')

# Routes
@app.route('/')
def index():
    events = Event.query.all()
    announcements = Announcement.query.order_by(Announcement.date_posted.desc()).limit(5).all()
    return render_template('index.html', events=events, announcements=announcements)

@app.route('/events')
def events():
    events = Event.query.all()
    return render_template('events.html', events=events)

@app.route('/event/<int:event_id>')
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('event_details.html', event=event)

@app.route('/event/register/<int:event_id>', methods=['POST'])
@login_required
def register_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if user is already registered
    existing_registration = EventRegistration.query.filter_by(
        user_id=current_user.id,
        event_id=event_id
    ).first()
    
    if existing_registration:
        flash('You are already registered for this event!', 'warning')
        return redirect(url_for('event_details', event_id=event_id))
    
    # Check if event is full
    if event.capacity and len(event.registrations) >= event.capacity:
        flash('Sorry, this event is already full!', 'error')
        return redirect(url_for('event_details', event_id=event_id))
    
    # Create new registration
    registration = EventRegistration(
        user_id=current_user.id,
        event_id=event_id
    )
    
    try:
        db.session.add(registration)
        db.session.commit()
        flash('Successfully registered for the event!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred during registration.', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_events = EventRegistration.query.filter_by(user_id=current_user.id).all()
    user_quizzes = QuizAttempt.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', registrations=user_events, quiz_attempts=user_quizzes)

# API Routes for CRUD operations
@app.route('/api/events', methods=['GET'])
def get_events():
    events = Event.query.all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'description': e.description,
        'date': e.date.strftime('%Y-%m-%d %H:%M'),
        'venue': e.venue,
        'capacity': e.capacity
    } for e in events])

@app.route('/api/announcements', methods=['GET'])
def get_announcements():
    announcements = Announcement.query.order_by(Announcement.date_posted.desc()).all()
    return jsonify([{
        'id': a.id,
        'title': a.title,
        'content': a.content,
        'date': a.date_posted.strftime('%Y-%m-%d %H:%M'),
        'priority': a.priority
    } for a in announcements])

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validation
        if not username or not email or not password or not confirm_password:
            flash('All fields are required!', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            is_admin=False
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration.', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.', 'error')
            return redirect(url_for('login'))
        
        # Log in user
        login_user(user, remember=remember)
        
        # Get the page they wanted to access (if any)
        next_page = request.args.get('next')
        
        flash('Logged in successfully!', 'success')
        return redirect(next_page or url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    try:
        current_user.username = request.form.get('username', current_user.username)
        current_user.email = request.form.get('email', current_user.email)
        
        # Update password if provided
        new_password = request.form.get('new_password')
        if new_password:
            current_password = request.form.get('current_password')
            if not check_password_hash(current_user.password, current_password):
                flash('Current password is incorrect!', 'error')
                return redirect(url_for('profile'))
            current_user.password = generate_password_hash(new_password)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating profile.', 'error')
    
    return redirect(url_for('profile'))

# Quiz Routes
@app.route('/quizzes')
def quizzes():
    quizzes = Quiz.query.all()
    return render_template('quizzes.html', quizzes=quizzes)

@app.route('/quiz/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    # Check if user has already completed this quiz
    existing_attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        completed=True
    ).first()
    
    if existing_attempt:
        flash('You have already completed this quiz!', 'info')
        return redirect(url_for('quiz_results', attempt_id=existing_attempt.id))
    
    return render_template('take_quiz.html', quiz=quiz)

@app.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Create or get existing attempt
    attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        completed=False
    ).first()
    
    if not attempt:
        attempt = QuizAttempt(user_id=current_user.id, quiz_id=quiz_id)
    
    # Calculate score
    score = 0
    total_questions = len(quiz.questions)
    
    for question in quiz.questions:
        answer = request.form.get(f'question_{question.id}')
        if answer == question.correct_answer:
            score += 1
    
    # Update attempt
    attempt.score = score
    attempt.completed = True
    attempt.attempt_date = datetime.utcnow()
    
    try:
        db.session.add(attempt)
        db.session.commit()
        flash(f'Quiz completed! Your score: {score}/{total_questions}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while submitting the quiz.', 'error')
    
    return redirect(url_for('quiz_results', attempt_id=attempt.id))

@app.route('/quiz/results/<int:attempt_id>')
@login_required
def quiz_results(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to view these results.', 'error')
        return redirect(url_for('quizzes'))
    
    return render_template('quiz_results.html', attempt=attempt)

def init_db():
    """Initialize the database and create tables"""
    try:
        # Create all tables if they don't exist
        db.create_all()
        
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
            
            # Add sample event
            event = Event(
                name='Welcome Fest 2024',
                description='Annual college welcome festival',
                date=datetime(2024, 3, 15, 10, 0),
                venue='College Auditorium',
                capacity=200
            )
            db.session.add(event)
            
            # Add sample announcement
            announcement = Announcement(
                title='Welcome to College Fest 2024',
                content='Get ready for the biggest college fest of the year!',
                priority='high'
            )
            db.session.add(announcement)
            
            # Add sample quiz
            quiz = Quiz(
                title='College Trivia',
                description='Test your knowledge about our college'
            )
            db.session.add(quiz)
            db.session.commit()  # Commit to get quiz ID
            
            # Add sample questions
            questions = [
                {
                    'text': 'What year was our college founded?',
                    'options': ['1960', '1965', '1970', '1975'],
                    'correct': '1965'
                },
                {
                    'text': 'Who is the current college principal?',
                    'options': ['Dr. Smith', 'Dr. Johnson', 'Dr. Williams', 'Dr. Brown'],
                    'correct': 'Dr. Smith'
                },
                {
                    'text': 'How many departments does our college have?',
                    'options': ['5', '7', '10', '12'],
                    'correct': '7'
                }
            ]
            
            for q_data in questions:
                question = Question(
                    quiz_id=quiz.id,
                    question_text=q_data['text'],
                    correct_answer=q_data['correct']
                )
                question.set_options(q_data['options'])
                db.session.add(question)
            
            db.session.commit()
            print("Sample data added successfully!")
    except Exception as e:
        print(f"Error during database initialization: {e}")
        db.session.rollback()
    finally:
        db.session.close()

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
