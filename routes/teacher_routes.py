from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from models import db, User, Teacher, Child, Group, Attendance, DailyNote, Media, Message, Schedule
from routes.auth_routes import teacher_required, login_required
from datetime import datetime, date
import os
from werkzeug.utils import secure_filename
import uuid
from models import db, User, Teacher, Child, Group, Attendance, DailyNote, Media, Message, Schedule, Parent

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@teacher_bp.route('/dashboard')
@teacher_required
def dashboard():
    user_id = session.get('user_id')
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    
    if not teacher:
        flash('Tarbiyachi profili topilmadi', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Get teacher's groups
    groups = Group.query.filter_by(teacher_id=teacher.id).all()
    
    # Get children in teacher's groups
    children = []
    for group in groups:
        children.extend(Child.query.filter_by(group_id=group.id).all())
    
    today = date.today()
    
    # Get today's schedule for teacher's groups
    day_of_week = today.weekday()  # 0 = Monday, 6 = Sunday
    schedules = []
    for group in groups:
        group_schedules = Schedule.query.filter_by(group_id=group.id, day_of_week=day_of_week).order_by(Schedule.start_time).all()
        schedules.extend(group_schedules)
    
    # Get unread messages
    unread_messages = Message.query.filter_by(teacher_id=teacher.id, read=False).count()
    
    return render_template('teacher/dashboard.html', 
                          teacher=teacher, 
                          groups=groups, 
                          children=children,
                          schedules=schedules,
                          today=today,
                          unread_messages=unread_messages,
                          now=datetime.now())  # `now` o‘zgaruvchisini qo‘shdik

@teacher_bp.route('/attendance', methods=['GET', 'POST'])
@teacher_required
def attendance():
    user_id = session.get('user_id')
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    
    if not teacher:
        flash('Tarbiyachi profili topilmadi', 'danger')
        return redirect(url_for('auth.logout'))
    
    selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    
    # Get groups assigned to this teacher
    groups = Group.query.filter_by(teacher_id=teacher.id).all()
    
    selected_group_id = request.args.get('group_id')
    if selected_group_id:
        selected_group = Group.query.get(selected_group_id)
        if selected_group not in groups:
            flash('Siz bu guruh uchun mas\'ul emassiz', 'danger')
            return redirect(url_for('teacher.attendance'))
    else:
        selected_group = groups[0] if groups else None
    
    if selected_group:
        children = Child.query.filter_by(group_id=selected_group.id).all()
    else:
        children = []
    
    if request.method == 'POST':
        for child in children:
            status = request.form.get(f'status_{child.id}')
            note = request.form.get(f'note_{child.id}')
            
            # Check if attendance record exists
            attendance = Attendance.query.filter_by(child_id=child.id, date=selected_date).first()
            
            if attendance:
                # Update existing record
                attendance.status = status
                attendance.note = note
            else:
                # Create new record
                attendance = Attendance(
                    child_id=child.id,
                    date=selected_date,
                    status=status,
                    note=note
                )
                db.session.add(attendance)
            
        db.session.commit()
        flash('Davomat muvaffaqiyatli saqlandi', 'success')
        return redirect(url_for('teacher.attendance', date=selected_date, group_id=selected_group.id))
    
    # Get existing attendance records
    attendance_records = {}
    if selected_group:
        for child in children:
            attendance = Attendance.query.filter_by(child_id=child.id, date=selected_date).first()
            if attendance:
                attendance_records[child.id] = attendance
    
    return render_template('teacher/attendance.html', 
                          teacher=teacher,
                          groups=groups,
                          selected_group=selected_group,
                          children=children,
                          selected_date=selected_date,
                          attendance_records=attendance_records,
                          now=datetime.now())  # `now` o‘zgaruvchisini qo‘shdik

@teacher_bp.route('/daily_notes', methods=['GET', 'POST'])
@teacher_required
def daily_notes():
    user_id = session.get('user_id')
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    
    if not teacher:
        flash('Tarbiyachi profili topilmadi', 'danger')
        return redirect(url_for('auth.logout'))
    
    selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    
    # Get children in teacher's groups
    groups = Group.query.filter_by(teacher_id=teacher.id).all()
    
    selected_child_id = request.args.get('child_id')
    if selected_child_id:
        selected_child = Child.query.get(selected_child_id)
        # Check if child is in teacher's group
        if selected_child.group_id not in [group.id for group in groups]:
            flash('Bu bola sizning guruhingizda emas', 'danger')
            return redirect(url_for('teacher.daily_notes'))
    else:
        # Get first child in first group
        if groups and groups[0].children:
            selected_child = groups[0].children[0]
        else:
            selected_child = None
    
    if request.method == 'POST' and selected_child:
        meal_notes = request.form.get('meal_notes')
        nap_notes = request.form.get('nap_notes')
        activity_notes = request.form.get('activity_notes')
        behavior_notes = request.form.get('behavior_notes')
        general_notes = request.form.get('general_notes')
        
        # Check if daily note exists
        daily_note = DailyNote.query.filter_by(
            child_id=selected_child.id, 
            teacher_id=teacher.id,
            date=selected_date
        ).first()
        
        if daily_note:
            # Update existing note
            daily_note.meal_notes = meal_notes
            daily_note.nap_notes = nap_notes
            daily_note.activity_notes = activity_notes
            daily_note.behavior_notes = behavior_notes
            daily_note.general_notes = general_notes
        else:
            # Create new note
            daily_note = DailyNote(
                child_id=selected_child.id,
                teacher_id=teacher.id,
                date=selected_date,
                meal_notes=meal_notes,
                nap_notes=nap_notes,
                activity_notes=activity_notes,
                behavior_notes=behavior_notes,
                general_notes=general_notes
            )
            db.session.add(daily_note)
        
        db.session.commit()
        flash('Kundalik yozuv muvaffaqiyatli saqlandi', 'success')
        return redirect(url_for('teacher.daily_notes', date=selected_date, child_id=selected_child.id))
    
    # Get all children in teacher's groups
    all_children = []
    for group in groups:
        all_children.extend(Child.query.filter_by(group_id=group.id).all())
    
    # Get existing daily note
    daily_note = None
    if selected_child:
        daily_note = DailyNote.query.filter_by(
            child_id=selected_child.id, 
            teacher_id=teacher.id,
            date=selected_date
        ).first()
    
    return render_template('teacher/daily_notes.html', 
                          teacher=teacher,
                          all_children=all_children,
                          selected_child=selected_child,
                          selected_date=selected_date,
                          daily_note=daily_note,
                          now=datetime.now())  # Add `now` here

@teacher_bp.route('/media', methods=['GET', 'POST'])
@teacher_required
def media():
    user_id = session.get('user_id')
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    
    if not teacher:
        flash('Tarbiyachi profili topilmadi', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Get children in teacher's groups
    groups = Group.query.filter_by(teacher_id=teacher.id).all()
    all_children = []
    for group in groups:
        all_children.extend(Child.query.filter_by(group_id=group.id).all())
    
    if request.method == 'POST':
        child_id = request.form.get('child_id')
        description = request.form.get('description')
        
        # Check if child is in teacher's group
        child = Child.query.get(child_id)
        if child.group_id not in [group.id for group in groups]:
            flash('Bu bola sizning guruhingizda emas', 'danger')
            return redirect(url_for('teacher.media'))
        
        # Check if file was submitted
        if 'media_file' not in request.files:
            flash('Fayl tanlanmagan', 'danger')
            return redirect(url_for('teacher.media'))
        
        file = request.files['media_file']
        
        if file.filename == '':
            flash('Fayl tanlanmagan', 'danger')
            return redirect(url_for('teacher.media'))
        
        # Determine media type
        media_type = request.form.get('media_type')
        
        if media_type == 'photo':
            allowed_extensions = current_app.config['ALLOWED_PHOTO_EXTENSIONS']
        else:  # video
            allowed_extensions = current_app.config['ALLOWED_VIDEO_EXTENSIONS']
        
        if file and allowed_file(file.filename, allowed_extensions):
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            # Save file to appropriate folder
            media_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], media_type + 's')
            if not os.path.exists(media_folder):
                os.makedirs(media_folder)
            
            file_path = os.path.join(media_folder, unique_filename)
            file.save(file_path)
            
            # Create media record in database
            new_media = Media(
                child_id=child_id,
                type=media_type,
                filename=f"{media_type}s/{unique_filename}",
                description=description,
                teacher_id=teacher.id
            )
            
            db.session.add(new_media)
            db.session.commit()
            
            flash('Media fayl muvaffaqiyatli yuklandi', 'success')
            return redirect(url_for('teacher.media'))
        else:
            flash(f"Noto'g'ri fayl formati. Ruxsat etilgan formatlar: {', '.join(allowed_extensions)}", 'danger')
            return redirect(url_for('teacher.media'))
    
    # Get uploaded media by teacher
    media_items = Media.query.filter_by(teacher_id=teacher.id).order_by(Media.upload_date.desc()).all()
    
    return render_template('teacher/media.html', 
                          teacher=teacher,
                          children=all_children,
                          media_items=media_items,
                          now=datetime.now())  # Add `now` here

@teacher_bp.route('/messages', methods=['GET', 'POST'])
@teacher_required
def messages():
    user_id = session.get('user_id')
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    
    if not teacher:
        flash('Tarbiyachi profili topilmadi', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Get children in teacher's groups
    groups = Group.query.filter_by(teacher_id=teacher.id).all()
    all_children = []
    parents = []
    
    for group in groups:
        children = Child.query.filter_by(group_id=group.id).all()
        all_children.extend(children)
        for child in children:
            if child.parent not in parents:
                parents.append(child.parent)
    
    selected_parent_id = request.args.get('parent_id')
    if selected_parent_id:
        selected_parent = Parent.query.get(selected_parent_id)
        # Check if parent has a child in teacher's group
        parent_children = Child.query.filter_by(parent_id=selected_parent.id).all()
        valid_parent = False
        for child in parent_children:
            if child.group_id in [group.id for group in groups]:
                valid_parent = True
                break
        
        if not valid_parent:
            flash('Bu ota-ona sizning guruhingiz bolalarining ota-onasi emas', 'danger')
            return redirect(url_for('teacher.messages'))
    else:
        selected_parent = parents[0] if parents else None
    
    if request.method == 'POST' and selected_parent:
        content = request.form.get('content')
        
        if not content:
            flash('Xabar matnini kiriting', 'danger')
            return redirect(url_for('teacher.messages', parent_id=selected_parent.id))
        
        new_message = Message(
            parent_id=selected_parent.id,
            teacher_id=teacher.id,
            sender_role='teacher',
            content=content
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        flash('Xabar yuborildi', 'success')
        return redirect(url_for('teacher.messages', parent_id=selected_parent.id))
    
    # Get conversation with selected parent
    conversation = []
    if selected_parent:
        conversation = Message.query.filter(
            ((Message.teacher_id == teacher.id) & (Message.parent_id == selected_parent.id))
        ).order_by(Message.sent_at).all()
        
        # Mark messages from parent as read
        for message in conversation:
            if message.sender_role == 'parent' and not message.read:
                message.read = True
        
        db.session.commit()
    
    return render_template('teacher/messages.html', 
                          teacher=teacher,
                          parents=parents,
                          selected_parent=selected_parent,
                          conversation=conversation,
                          now=datetime.now())  # Add `now` here

@teacher_bp.route('/schedule')
@teacher_required
def schedule():
    user_id = session.get('user_id')
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    
    if not teacher:
        flash('Tarbiyachi profili topilmadi', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Get groups assigned to this teacher
    groups = Group.query.filter_by(teacher_id=teacher.id).all()
    
    selected_group_id = request.args.get('group_id')
    if selected_group_id:
        selected_group = Group.query.get(selected_group_id)
        if selected_group not in groups:
            flash('Siz bu guruh uchun mas\'ul emassiz', 'danger')
            return redirect(url_for('teacher.schedule'))
    else:
        selected_group = groups[0] if groups else None
    
    # Get schedule for selected group
    schedule_by_day = {}
    if selected_group:
        for day in range(7):  # 0 = Monday, 6 = Sunday
            schedule_by_day[day] = Schedule.query.filter_by(
                group_id=selected_group.id, day_of_week=day
            ).order_by(Schedule.start_time).all()
    
    day_names = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']
    today_day = datetime.today().weekday()
    
    return render_template('teacher/schedule.html', 
                          teacher=teacher,
                          groups=groups,
                          selected_group=selected_group,
                          schedule_by_day=schedule_by_day,
                          day_names=day_names,
                          today_day=today_day,
                          now=datetime.now())  # `now` qo‘shildi