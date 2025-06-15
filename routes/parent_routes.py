from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, Parent, Child, DailyNote, Attendance, Media, Message, Payment, Group, Schedule,Teacher
from routes.auth_routes import parent_required
from datetime import datetime, date
from datetime import date, timedelta

thirty_days_ago = date.today() - timedelta(days=30)

parent_bp = Blueprint('parent', __name__, url_prefix='/parent')

@parent_bp.route('/dashboard')
@parent_required
def dashboard():
    user_id = session.get('user_id')
    parent = Parent.query.filter_by(user_id=user_id).first()
    
    if not parent:
        flash('Ota-ona profili topilmadi', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Get parent's children
    children = Child.query.filter_by(parent_id=parent.id).all()
    
    # Get today's attendance for parent's children
    today = date.today()
    attendance = {}
    for child in children:
        attendance[child.id] = Attendance.query.filter_by(child_id=child.id, date=today).first()
    
    # Get latest daily notes for parent's children
    latest_notes = {}
    for child in children:
        latest_note = DailyNote.query.filter_by(child_id=child.id).order_by(DailyNote.date.desc()).first()
        latest_notes[child.id] = latest_note
    
    # Get unread messages
    unread_messages = Message.query.filter_by(parent_id=parent.id, read=False).count()
    
    # Get recent media for parent's children
    recent_media = []
    for child in children:
        child_media = Media.query.filter_by(child_id=child.id).order_by(Media.upload_date.desc()).limit(3).all()
        recent_media.extend(child_media)
    
    # Sort recent media by upload date
    recent_media.sort(key=lambda x: x.upload_date, reverse=True)
    recent_media = recent_media[:5]  # Limit to 5 items
    
    return render_template('parent/dashboard.html', 
                          parent=parent, 
                          children=children,
                          attendance=attendance,
                          latest_notes=latest_notes,
                          unread_messages=unread_messages,
                          recent_media=recent_media)

@parent_bp.route('/child/<int:child_id>')
@parent_required
def child_info(child_id):
    user_id = session.get('user_id')
    parent = Parent.query.filter_by(user_id=user_id).first()
    
    if not parent:
        flash('Ota-ona profili topilmadi', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Check if child belongs to parent
    child = Child.query.filter_by(id=child_id, parent_id=parent.id).first()
    if not child:
        flash('Farzand topilmadi', 'danger')
        return redirect(url_for('parent.dashboard'))
    
    # Get group information
    group = Group.query.get(child.group_id) if child.group_id else None
    
    # Get attendance history (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)

    attendance_history = Attendance.query.filter(
        Attendance.child_id == child.id,
        Attendance.date >= thirty_days_ago
    ).order_by(Attendance.date.desc()).all()
    
    # Get daily notes history
    daily_notes = DailyNote.query.filter_by(child_id=child.id).order_by(DailyNote.date.desc()).all()
    
    return render_template('parent/child_info.html', 
                          parent=parent,
                          child=child,
                          group=group,
                          attendance_history=attendance_history,
                          daily_notes=daily_notes)

@parent_bp.route('/schedule')
@parent_required
def schedule():
    user_id = session.get('user_id')
    parent = Parent.query.filter_by(user_id=user_id).first()
    
    if not parent:
        flash('Ota-ona profili topilmadi', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Get parent's children
    children = Child.query.filter_by(parent_id=parent.id).all()
    
    selected_child_id = request.args.get('child_id')
    if selected_child_id:
        selected_child = Child.query.filter_by(id=selected_child_id, parent_id=parent.id).first()
        if not selected_child:
            flash('Farzand topilmadi', 'danger')
            return redirect(url_for('parent.schedule'))
    else:
        selected_child = children[0] if children else None
    
    # Get schedule for selected child's group
    schedule_by_day = {}
    if selected_child and selected_child.group_id:
        for day in range(7):  # 0 = Monday, 6 = Sunday
            schedule_by_day[day] = Schedule.query.filter_by(
                group_id=selected_child.group_id, day_of_week=day
            ).order_by(Schedule.start_time).all()
    
    day_names = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']
    today_day = datetime.today().weekday()
    
    return render_template('parent/schedule.html', 
                          parent=parent,
                          children=children,
                          selected_child=selected_child,
                          schedule_by_day=schedule_by_day,
                          day_names=day_names,
                          today_day=today_day)

@parent_bp.route('/gallery')
@parent_required
def gallery():
    user_id = session.get('user_id')
    parent = Parent.query.filter_by(user_id=user_id).first()
    
    if not parent:
        flash('Ota-ona profili topilmadi', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Get parent's children
    children = Child.query.filter_by(parent_id=parent.id).all()
    child_ids = [child.id for child in children]
    
    media_type = request.args.get('type', 'photo')  # Default to photos
    
    # Get media for parent's children
    if media_type == 'all':
        media_items = Media.query.filter(Media.child_id.in_(child_ids)).order_by(Media.upload_date.desc()).all()
    else:
        media_items = Media.query.filter(
            Media.child_id.in_(child_ids),
            Media.type == media_type
        ).order_by(Media.upload_date.desc()).all()
    
    return render_template('parent/gallery.html', 
                          parent=parent,
                          children=children,
                          media_items=media_items,
                          media_type=media_type)

@parent_bp.route('/messages', methods=['GET', 'POST'])
@parent_required
def messages():
    user_id = session.get('user_id')
    parent = Parent.query.filter_by(user_id=user_id).first()
    
    if not parent:
        flash('Ota-ona profili topilmadi', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Get parent's children
    children = Child.query.filter_by(parent_id=parent.id).all()
    
    # Get teachers of parent's children
    teachers = []
    for child in children:
        if child.group and child.group.teacher and child.group.teacher not in teachers:
            teachers.append(child.group.teacher)
    
    # Preprocess group names for each teacher
    teacher_group_map = {}
    for teacher in teachers:
        group_name = None
        for group in teacher.groups:
            for child in children:
                if child.group_id == group.id:
                    group_name = group.name
                    break
            if group_name:
                break
        teacher_group_map[teacher.id] = group_name or '-'
    
    selected_teacher_id = request.args.get('teacher_id')
    if selected_teacher_id:
        selected_teacher = Teacher.query.get(selected_teacher_id)
        if selected_teacher not in teachers:
            flash('Bu tarbiyachi sizning bolalaringizga mas\'ul emas', 'danger')
            return redirect(url_for('parent.messages'))
    else:
        selected_teacher = teachers[0] if teachers else None
    
    if request.method == 'POST' and selected_teacher:
        content = request.form.get('content')
        
        if not content:
            flash('Xabar matnini kiriting', 'danger')
            return redirect(url_for('parent.messages', teacher_id=selected_teacher.id))
        
        new_message = Message(
            parent_id=parent.id,
            teacher_id=selected_teacher.id,
            sender_role='parent',
            content=content
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        flash('Xabar yuborildi', 'success')
        return redirect(url_for('parent.messages', teacher_id=selected_teacher.id))
    
    # Get conversation with selected teacher
    conversation = []
    if selected_teacher:
        conversation = Message.query.filter(
            ((Message.teacher_id == selected_teacher.id) & (Message.parent_id == parent.id))
        ).order_by(Message.sent_at).all()
        
        # Mark messages from teacher as read
        for message in conversation:
            if message.sender_role == 'teacher' and not message.read:
                message.read = True
        
        db.session.commit()
    
    return render_template('parent/messages.html', 
                          parent=parent,
                          teachers=teachers,
                          selected_teacher=selected_teacher,
                          conversation=conversation,
                          children=children,
                          teacher_group_map=teacher_group_map)

@parent_bp.route('/payments')
@parent_required
def payments():
    user_id = session.get('user_id')
    parent = Parent.query.filter_by(user_id=user_id).first()
    
    if not parent:
        flash('Ota-ona profili topilmadi', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Get parent's children
    children = Child.query.filter_by(parent_id=parent.id).all()
    child_ids = [child.id for child in children]
    
    # Get payment history
    payments = Payment.query.filter(Payment.child_id.in_(child_ids)).order_by(Payment.payment_date.desc()).all()
    
    # Group payments by child
    payments_by_child = {}
    for child in children:
        payments_by_child[child.id] = []
    
    for payment in payments:
        payments_by_child[payment.child_id].append(payment)
    
    return render_template('parent/payments.html', 
                          parent=parent,
                          children=children,
                          payments=payments,
                          payments_by_child=payments_by_child)
