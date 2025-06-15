from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'teacher', 'parent'
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False, cascade='all, delete-orphan')
    parent_profile = db.relationship('Parent', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def __init__(self, username, password, role, first_name, last_name, email, phone=None):
        self.username = username
        self.set_password(password)
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    qualification = db.Column(db.String(100))
    bio = db.Column(db.Text)
    
    # Relationships
    groups = db.relationship('Group', backref='teacher', lazy=True)
    daily_notes = db.relationship('DailyNote', backref='teacher', lazy=True)
    messages = db.relationship('Message', backref='teacher', foreign_keys='Message.teacher_id', lazy=True)


class Parent(db.Model):
    __tablename__ = 'parents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    address = db.Column(db.String(200))
    
    # Relationships
    children = db.relationship('Child', backref='parent', lazy=True)
    messages = db.relationship('Message', backref='parent', foreign_keys='Message.parent_id', lazy=True)


class Child(db.Model):
    __tablename__ = 'children'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10))
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    allergies = db.Column(db.Text)
    medical_notes = db.Column(db.Text)
    enrollment_date = db.Column(db.Date, default=datetime.utcnow().date())
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='child', lazy=True)
    daily_notes = db.relationship('DailyNote', backref='child', lazy=True)
    media_items = db.relationship('Media', backref='child', lazy=True)
    payments = db.relationship('Payment', backref='child', lazy=True)


class Group(db.Model):
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    capacity = db.Column(db.Integer, default=20)
    description = db.Column(db.Text)
    age_group = db.Column(db.String(20))  # e.g., '2-3 years', '4-5 years'
    
    # Relationships
    children = db.relationship('Child', backref='group', lazy=True)
    schedules = db.relationship('Schedule', backref='group', lazy=True)


class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'present', 'absent', 'late', 'excused'
    note = db.Column(db.Text)
    
    __table_args__ = (db.UniqueConstraint('child_id', 'date', name='unique_child_date'),)


class DailyNote(db.Model):
    __tablename__ = 'daily_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    meal_notes = db.Column(db.Text)
    nap_notes = db.Column(db.Text)
    activity_notes = db.Column(db.Text)
    behavior_notes = db.Column(db.Text)
    general_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('child_id', 'date', name='unique_child_date_note'),)


class Media(db.Model):
    __tablename__ = 'media'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'photo', 'video'
    filename = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    sender_role = db.Column(db.String(20), nullable=False)  # 'teacher', 'parent'
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)


class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0 = Monday, 6 = Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    activity = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    __table_args__ = (db.UniqueConstraint('group_id', 'day_of_week', 'start_time', name='unique_schedule_slot'),)


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_type = db.Column(db.String(20), nullable=False)  # 'cash', 'card', 'transfer'
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False)  # 'paid', 'pending', 'cancelled'
    month = db.Column(db.Integer, nullable=False)  # 1 = January, 12 = December
    year = db.Column(db.Integer, nullable=False)