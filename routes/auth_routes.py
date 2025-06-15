from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import User, db
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Iltimos, avval tizimga kiring', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Iltimos, avval tizimga kiring', 'warning')
            return redirect(url_for('auth.login'))
        
        if session.get('role') != 'admin':
            flash('Bu sahifa faqat administratorlar uchun', 'danger')
            return redirect(url_for('auth.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Iltimos, avval tizimga kiring', 'warning')
            return redirect(url_for('auth.login'))
        
        if session.get('role') != 'teacher' and session.get('role') != 'admin':
            flash('Bu sahifa faqat tarbiyachilar uchun', 'danger')
            return redirect(url_for('auth.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def parent_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Iltimos, avval tizimga kiring', 'warning')
            return redirect(url_for('auth.login'))
        
        if session.get('role') != 'parent' and session.get('role') != 'admin':
            flash('Bu sahifa faqat ota-onalar uchun', 'danger')
            return redirect(url_for('auth.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['name'] = f"{user.first_name} {user.last_name}"
            
            flash(f"Xush kelibsiz, {user.first_name}!", 'success')
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Noto\'g\'ri foydalanuvchi nomi yoki parol', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Siz tizimdan chiqdingiz', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    
    if role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher.dashboard'))
    elif role == 'parent':
        return redirect(url_for('parent.dashboard'))
    else:
        flash('Noma\'lum foydalanuvchi roli', 'danger')
        return redirect(url_for('auth.logout'))

from datetime import datetime  # datetime moduli import qilinadi

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        flash('Foydalanuvchi topilmadi', 'danger')
        return redirect(url_for('auth.logout'))
    
    if request.method == 'POST':
        # Update user profile
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        
        # Check if password is being updated
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if current_password and new_password and confirm_password:
            if not user.check_password(current_password):
                flash('Joriy parol noto\'g\'ri', 'danger')
                return render_template('profile.html', user=user, now=datetime.now())
            
            if new_password != confirm_password:
                flash('Yangi parollar mos kelmaydi', 'danger')
                return render_template('profile.html', user=user, now=datetime.now())
            
            user.set_password(new_password)
            flash('Parol muvaffaqiyatli yangilandi', 'success')
        
        db.session.commit()
        flash('Profil muvaffaqiyatli yangilandi', 'success')
        
        # Update session name
        session['name'] = f"{user.first_name} {user.last_name}"
        
        return redirect(url_for('auth.profile'))
    
    return render_template('profile.html', user=user, now=datetime.now())