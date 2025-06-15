from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, Teacher, Parent, Child, Group, Schedule, Payment
from routes.auth_routes import admin_required
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

from datetime import datetime

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    teacher_count = Teacher.query.count()
    child_count = Child.query.count()
    parent_count = Parent.query.count()
    group_count = Group.query.count()
    
    recent_children = Child.query.order_by(Child.enrollment_date.desc()).limit(5).all()
    recent_payments = Payment.query.order_by(Payment.payment_date.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          teacher_count=teacher_count,
                          child_count=child_count,
                          parent_count=parent_count,
                          group_count=group_count,
                          recent_children=recent_children,
                          recent_payments=recent_payments,
                          now=datetime.now())  # `now` o‘zgaruvchisini qo‘shdik
# Teacher Management
@admin_bp.route('/teachers')
@admin_required
def teachers():
    teachers = Teacher.query.join(User).all()
    return render_template('admin/teachers.html', teachers=teachers)

@admin_bp.route('/teachers/add', methods=['GET', 'POST'])
@admin_required
def add_teacher():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        qualification = request.form.get('qualification')
        bio = request.form.get('bio')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Bu foydalanuvchi nomi allaqachon mavjud', 'danger')
            return render_template('admin/add_teacher.html', now=datetime.now())
        
        if User.query.filter_by(email=email).first():
            flash('Bu email allaqachon ro\'yxatdan o\'tgan', 'danger')
            return render_template('admin/add_teacher.html', now=datetime.now())
        
        # Create user with teacher role
        new_user = User(username=username, password=password, role='teacher',
                      first_name=first_name, last_name=last_name, email=email, phone=phone)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create teacher profile
        new_teacher = Teacher(user_id=new_user.id, qualification=qualification, bio=bio)
        db.session.add(new_teacher)
        db.session.commit()
        
        flash('Tarbiyachi muvaffaqiyatli qo\'shildi', 'success')
        return redirect(url_for('admin.teachers'))
    
    return render_template('admin/add_teacher.html', now=datetime.now())

@admin_bp.route('/teachers/edit/<int:teacher_id>', methods=['GET', 'POST'])
@admin_required
def edit_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    user = User.query.get(teacher.user_id)
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        
        teacher.qualification = request.form.get('qualification')
        teacher.bio = request.form.get('bio')
        
        # Update password if provided
        new_password = request.form.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        flash('Tarbiyachi ma\'lumotlari yangilandi', 'success')
        return redirect(url_for('admin.teachers'))
    
    return render_template('admin/edit_teacher.html', teacher=teacher, user=user)

@admin_bp.route('/teachers/delete/<int:teacher_id>', methods=['POST'])
@admin_required
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    user = User.query.get(teacher.user_id)
    
    # Check if teacher has assigned groups
    if teacher.groups:
        flash('Bu tarbiyachi guruhlarga biriktirilgan, avval boshqa tarbiyachi tayinlang', 'danger')
        return redirect(url_for('admin.teachers'))
    
    db.session.delete(user)  # This will cascade delete the teacher profile
    db.session.commit()
    
    flash('Tarbiyachi o\'chirildi', 'success')
    return redirect(url_for('admin.teachers'))

# Child Management
@admin_bp.route('/children')
@admin_required
def children():
    children = Child.query.all()
    return render_template('admin/children.html', children=children)

@admin_bp.route('/children/add', methods=['GET', 'POST'])
@admin_required
def add_child():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
        gender = request.form.get('gender')
        parent_id = request.form.get('parent_id')
        group_id = request.form.get('group_id') or None
        allergies = request.form.get('allergies')
        medical_notes = request.form.get('medical_notes')
        enrollment_date = datetime.strptime(request.form.get('enrollment_date'), '%Y-%m-%d').date()
        
        new_child = Child(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            gender=gender,
            parent_id=parent_id,
            group_id=group_id,
            allergies=allergies,
            medical_notes=medical_notes,
            enrollment_date=enrollment_date
        )
        
        db.session.add(new_child)
        db.session.commit()
        
        flash('Bola muvaffaqiyatli qo\'shildi', 'success')
        return redirect(url_for('admin.children'))
    
    parents = Parent.query.join(User).all()
    groups = Group.query.all()
    
    return render_template('admin/add_child.html', parents=parents, groups=groups, now=datetime.now())

@admin_bp.route('/children/edit/<int:child_id>', methods=['GET', 'POST'])
@admin_required
def edit_child(child_id):
    child = Child.query.get_or_404(child_id)
    
    if request.method == 'POST':
        child.first_name = request.form.get('first_name')
        child.last_name = request.form.get('last_name')
        child.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
        child.gender = request.form.get('gender')
        child.parent_id = request.form.get('parent_id')
        child.group_id = request.form.get('group_id') or None
        child.allergies = request.form.get('allergies')
        child.medical_notes = request.form.get('medical_notes')
        child.enrollment_date = datetime.strptime(request.form.get('enrollment_date'), '%Y-%m-%d').date()
        
        db.session.commit()
        flash('Bola ma\'lumotlari yangilandi', 'success')
        return redirect(url_for('admin.children'))
    
    parents = Parent.query.join(User).all()
    groups = Group.query.all()
    
    return render_template('admin/edit_child.html', child=child, parents=parents, groups=groups)

@admin_bp.route('/children/delete/<int:child_id>', methods=['POST'])
@admin_required
def delete_child(child_id):
    child = Child.query.get_or_404(child_id)
    
    db.session.delete(child)
    db.session.commit()
    
    flash('Bola ma\'lumotlari o\'chirildi', 'success')
    return redirect(url_for('admin.children'))

# Parent Management
@admin_bp.route('/parents')
@admin_required
def parents():
    parents = Parent.query.join(User).all()
    return render_template('admin/parents.html', parents=parents)

from datetime import datetime  # Agar hali import qilinmagan bo‘lsa

@admin_bp.route('/parents/add', methods=['GET', 'POST'])
@admin_required
def add_parent():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Bu foydalanuvchi nomi allaqachon mavjud', 'danger')
            return render_template('admin/add_parent.html', now=datetime.now())
        
        if User.query.filter_by(email=email).first():
            flash('Bu email allaqachon ro\'yxatdan o\'tgan', 'danger')
            return render_template('admin/add_parent.html', now=datetime.now())
        
        # Create user with parent role
        new_user = User(
            username=username,
            password=password,
            role='parent',
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create parent profile
        new_parent = Parent(user_id=new_user.id, address=address)
        db.session.add(new_parent)
        db.session.commit()
        
        flash('Ota-ona muvaffaqiyatli qo\'shildi', 'success')
        return redirect(url_for('admin.parents'))
    
    return render_template('admin/add_parent.html', now=datetime.now())

@admin_bp.route('/parents/edit/<int:parent_id>', methods=['GET', 'POST'])
@admin_required
def edit_parent(parent_id):
    parent = Parent.query.get_or_404(parent_id)
    user = User.query.get(parent.user_id)
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        
        parent.address = request.form.get('address')
        
        # Update password if provided
        new_password = request.form.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        flash('Ota-ona ma\'lumotlari yangilandi', 'success')
        return redirect(url_for('admin.parents'))
    
    return render_template('admin/edit_parent.html', parent=parent, user=user)

@admin_bp.route('/parents/delete/<int:parent_id>', methods=['POST'])
@admin_required
def delete_parent(parent_id):
    parent = Parent.query.get_or_404(parent_id)
    user = User.query.get(parent.user_id)
    
    # Check if parent has children
    if parent.children:
        flash('Bu ota-onaning bolalari mavjud, avval bolalarni o\'chiring', 'danger')
        return redirect(url_for('admin.parents'))
    
    db.session.delete(user)  # This will cascade delete the parent profile
    db.session.commit()
    
    flash('Ota-ona ma\'lumotlari o\'chirildi', 'success')
    return redirect(url_for('admin.parents'))

# Group Management
@admin_bp.route('/groups')
@admin_required
def groups():
    groups = Group.query.all()
    return render_template('admin/groups.html', groups=groups)

from datetime import datetime

@admin_bp.route('/groups/add', methods=['GET', 'POST'])
@admin_required
def add_group():
    if request.method == 'POST':
        name = request.form.get('name')
        teacher_id = request.form.get('teacher_id') or None
        capacity = request.form.get('capacity')
        description = request.form.get('description')
        age_group = request.form.get('age_group')
        
        new_group = Group(
            name=name,
            teacher_id=teacher_id,
            capacity=capacity,
            description=description,
            age_group=age_group
        )
        
        db.session.add(new_group)
        db.session.commit()
        
        flash('Guruh muvaffaqiyatli qo\'shildi', 'success')
        return redirect(url_for('admin.groups'))
    
    teachers = Teacher.query.join(User).all()
    return render_template('admin/add_group.html', teachers=teachers, now=datetime.now())

@admin_bp.route('/groups/edit/<int:group_id>', methods=['GET', 'POST'])
@admin_required
def edit_group(group_id):
    group = Group.query.get_or_404(group_id)
    
    if request.method == 'POST':
        group.name = request.form.get('name')
        group.teacher_id = request.form.get('teacher_id') or None
        group.capacity = request.form.get('capacity')
        group.description = request.form.get('description')
        group.age_group = request.form.get('age_group')
        
        db.session.commit()
        flash('Guruh ma\'lumotlari yangilandi', 'success')
        return redirect(url_for('admin.groups'))
    
    teachers = Teacher.query.join(User).all()
    return render_template('admin/edit_group.html', group=group, teachers=teachers, now=datetime.now())

@admin_bp.route('/groups/delete/<int:group_id>', methods=['POST'])
@admin_required
def delete_group(group_id):
    group = Group.query.get_or_404(group_id)
    
    # Check if group has children
    if group.children:
        flash('Bu guruhda bolalar bor, avval bolalarni boshqa guruhga o\'tkazing', 'danger')
        return redirect(url_for('admin.groups'))
    
    db.session.delete(group)
    db.session.commit()
    
    flash('Guruh o\'chirildi', 'success')
    return redirect(url_for('admin.groups'))

# Schedule Management
@admin_bp.route('/schedule')
@admin_required
def schedule():
    groups = Group.query.all()
    schedules = Schedule.query.all()
    
    schedule_by_group = {}
    for group in groups:
        schedule_by_group[group.id] = []
        for day in range(7):  # 0 = Monday, 6 = Sunday
            schedule_by_group[group.id].append([])
    
    for schedule in schedules:
        schedule_by_group[schedule.group_id][schedule.day_of_week].append(schedule)
    
    day_names = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']
    
    return render_template('admin/schedule.html', groups=groups, schedule_by_group=schedule_by_group, day_names=day_names)

@admin_bp.route('/schedule/add', methods=['GET', 'POST'])
@admin_required
def add_schedule():
    if request.method == 'POST':
        group_id = request.form.get('group_id')
        day_of_week = int(request.form.get('day_of_week'))  # 0 = Monday, 6 = Sunday
        start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
        activity = request.form.get('activity')
        description = request.form.get('description')
        
        # Check for time conflicts
        existing_schedules = Schedule.query.filter_by(group_id=group_id, day_of_week=day_of_week).all()
        for existing in existing_schedules:
            if (start_time <= existing.end_time and end_time >= existing.start_time):
                flash('Bu vaqtda boshqa mashg\'ulot bor', 'danger')
                return redirect(url_for('admin.add_schedule'))
        
        new_schedule = Schedule(
            group_id=group_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            activity=activity,
            description=description
            
            
        )
        
        db.session.add(new_schedule)
        db.session.commit()
        
        flash('Jadval muvaffaqiyatli qo\'shildi', 'success')
        return redirect(url_for('admin.schedule'))
    
    groups = Group.query.all()
    day_names = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']
    
    return render_template('admin/add_schedule.html', groups=groups, day_names=day_names)

@admin_bp.route('/schedule/edit/<int:schedule_id>', methods=['GET', 'POST'])
@admin_required
def edit_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    
    if request.method == 'POST':
        group_id = request.form.get('group_id')
        day_of_week = int(request.form.get('day_of_week'))
        start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
        activity = request.form.get('activity')
        description = request.form.get('description')
        
        # Check for time conflicts (excluding current schedule)
        existing_schedules = Schedule.query.filter(
            Schedule.group_id == group_id,
            Schedule.day_of_week == day_of_week,
            Schedule.id != schedule_id
        ).all()
        
        for existing in existing_schedules:
            if (start_time <= existing.end_time and end_time >= existing.start_time):
                flash('Bu vaqtda boshqa mashg\'ulot bor', 'danger')
                return redirect(url_for('admin.edit_schedule', schedule_id=schedule_id))
        
        schedule.group_id = group_id
        schedule.day_of_week = day_of_week
        schedule.start_time = start_time
        schedule.end_time = end_time
        schedule.activity = activity
        schedule.description = description
        
        db.session.commit()
        flash('Jadval muvaffaqiyatli yangilandi', 'success')
        return redirect(url_for('admin.schedule'))
    
    groups = Group.query.all()
    day_names = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']
    
    return render_template('admin/edit_schedule.html', schedule=schedule, groups=groups, day_names=day_names)

@admin_bp.route('/schedule/delete/<int:schedule_id>', methods=['POST'])
@admin_required
def delete_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    
    db.session.delete(schedule)
    db.session.commit()
    
    flash('Jadval muvaffaqiyatli o\'chirildi', 'success')
    return redirect(url_for('admin.schedule'))

# Payment Management
@admin_bp.route('/payments')
@admin_required
def payments():
    payments = Payment.query.order_by(Payment.payment_date.desc()).all()
    return render_template('admin/payments.html', payments=payments)

@admin_bp.route('/payments/add', methods=['GET', 'POST'])
@admin_required
def add_payment():
    if request.method == 'POST':
        child_id = request.form.get('child_id')
        amount = float(request.form.get('amount'))
        payment_date = datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date()
        payment_type = request.form.get('payment_type')
        description = request.form.get('description')
        status = request.form.get('status')
        month = int(request.form.get('month'))
        year = int(request.form.get('year'))
        
        new_payment = Payment(
            child_id=child_id,
            amount=amount,
            payment_date=payment_date,
            payment_type=payment_type,
            description=description,
            status=status,
            month=month,
            year=year
        )
        
        db.session.add(new_payment)
        db.session.commit()
        
        flash('To\'lov muvaffaqiyatli qo\'shildi', 'success')
        return redirect(url_for('admin.payments'))
    
    children = Child.query.all()
    current_year = datetime.now().year
    years = list(range(current_year - 2, current_year + 2))
    
    return render_template('admin/add_payment.html', children=children, years=years)

@admin_bp.route('/payments/edit/<int:payment_id>', methods=['GET', 'POST'])
@admin_required
def edit_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    if request.method == 'POST':
        payment.child_id = request.form.get('child_id')
        payment.amount = float(request.form.get('amount'))
        payment.payment_date = datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date()
        payment.payment_type = request.form.get('payment_type')
        payment.description = request.form.get('description')
        payment.status = request.form.get('status')
        payment.month = int(request.form.get('month'))
        payment.year = int(request.form.get('year'))
        
        db.session.commit()
        flash('To\'lov muvaffaqiyatli yangilandi', 'success')
        return redirect(url_for('admin.payments'))
    
    children = Child.query.all()
    current_year = datetime.now().year
    years = list(range(current_year - 2, current_year + 2))
    
    return render_template('admin/edit_payment.html', payment=payment, children=children, years=years)

@admin_bp.route('/payments/delete/<int:payment_id>', methods=['POST'])
@admin_required
def delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    db.session.delete(payment)
    db.session.commit()
    
    flash('To\'lov muvaffaqiyatli o\'chirildi', 'success')
    return redirect(url_for('admin.payments'))

# Reports
@admin_bp.route('/reports')
@admin_required
def reports():
    return render_template('admin/reports.html')

@admin_bp.route('/reports/payments', methods=['GET', 'POST'])
@admin_required
def payment_reports():
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        month = request.form.get('month')
        year = request.form.get('year')
        
        if report_type == 'monthly':
            payments = Payment.query.filter_by(month=month, year=year).all()
        elif report_type == 'yearly':
            payments = Payment.query.filter_by(year=year).all()
        else:
            payments = Payment.query.all()
        
        total_amount = sum(payment.amount for payment in payments if payment.status == 'paid')
        pending_amount = sum(payment.amount for payment in payments if payment.status == 'pending')
        
        return render_template('admin/payment_report.html', 
                              payments=payments, 
                              total_amount=total_amount,
                              pending_amount=pending_amount,
                              report_type=report_type,
                              month=month,
                              year=year)
    
    current_year = datetime.now().year
    years = list(range(current_year - 2, current_year + 2))
    
    return render_template('admin/payment_report_form.html', years=years)