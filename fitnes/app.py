from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import os
import pymysql

# Replace MySQL-python with PyMySQL
pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Update database configuration with PyMySQL
try:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/gym_system'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)
except Exception as e:
    print(f"Database connection error: {e}")
    raise

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    schedules = db.relationship('Schedule', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    schedule_date = db.Column(db.Date, nullable=False)
    schedule_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    health_declaration = db.relationship('HealthDeclaration', backref='schedule', uselist=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class HealthDeclaration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    has_fever = db.Column(db.Boolean, default=False)
    has_cough = db.Column(db.Boolean, default=False)
    has_cold = db.Column(db.Boolean, default=False)
    has_sore_throat = db.Column(db.Boolean, default=False)
    has_breathing_problems = db.Column(db.Boolean, default=False)
    has_diarrhea = db.Column(db.Boolean, default=False)
    has_body_pains = db.Column(db.Boolean, default=False)
    has_travelled = db.Column(db.Boolean, default=False)
    has_contact_with_covid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(email=email, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        # Get statistics for admin dashboard
        total_users = User.query.count()
        total_schedules = Schedule.query.count()
        pending_schedules = Schedule.query.filter_by(status='pending').count()
        today_schedules = Schedule.query.filter(
            db.func.date(Schedule.schedule_date) == datetime.now().date()
        ).count()
        
        return render_template('admin/dashboard.html',
                            total_users=total_users,
                            total_schedules=total_schedules,
                            pending_schedules=pending_schedules,
                            today_schedules=today_schedules)
    else:
        # Regular user dashboard
        schedules = Schedule.query.filter_by(user_id=current_user.id).all()
        today = datetime.now().date()
        return render_template('dashboard.html', schedules=schedules, today=today)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    if request.method == 'POST':
        schedule_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        
        # Check if date is already full
        total_schedules = Schedule.query.filter(
            Schedule.schedule_date == schedule_date,
            Schedule.status.in_(['approved', 'pending'])
        ).count()
        
        if total_schedules >= 30:
            flash('Sorry, the selected date has reached the maximum capacity of 30 users. Please choose another date.', 'error')
            return redirect(url_for('dashboard'))
        
        # Create new schedule
        new_schedule = Schedule(
            user_id=current_user.id,
            age=request.form.get('age'),
            address=request.form.get('address'),
            schedule_date=schedule_date,
            schedule_time=datetime.strptime(request.form.get('time'), '%H:%M').time(),
            status='pending'
        )
        db.session.add(new_schedule)
        db.session.flush()

        # Create health declaration
        health_declaration = HealthDeclaration(
            schedule_id=new_schedule.id,
            has_fever=request.form.get('fever') == 'yes',
            has_cough=request.form.get('cough') == 'yes',
            has_cold=request.form.get('cold') == 'yes',
            has_sore_throat=request.form.get('sore_throat') == 'yes',
            has_breathing_problems=request.form.get('breathing_problems') == 'yes',
            has_diarrhea=request.form.get('diarrhea') == 'yes',
            has_body_pains=request.form.get('body_pains') == 'yes',
            has_travelled=request.form.get('travelled') == 'yes',
            has_contact_with_covid=request.form.get('covid_contact') == 'yes'
        )
        db.session.add(health_declaration)
        db.session.commit()

        flash('Schedule and health declaration submitted successfully!')
        return redirect(url_for('dashboard'))

    return render_template('schedule_form.html')

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def user_management():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Handle new user creation
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
        else:
            new_user = User(email=email, name=name, is_admin=is_admin)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('User created successfully!', 'success')
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>/edit', methods=['POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    try:
        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        user.is_admin = data.get('is_admin', user.is_admin)
        
        if data.get('password'):
            user.set_password(data['password'])
        
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'is_admin': user.is_admin
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    user = User.query.get_or_404(user_id)
    try:
        # Delete associated schedules and health declarations
        for schedule in user.schedules:
            if schedule.health_declaration:
                db.session.delete(schedule.health_declaration)
            db.session.delete(schedule)
        
        db.session.delete(user)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'User deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/admin/schedules')
@login_required
def view_schedules():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query for approved schedules
    query = Schedule.query.filter_by(status='approved').join(User)
    
    # Apply date filters if provided
    if start_date:
        query = query.filter(Schedule.schedule_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Schedule.schedule_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    # Order by date and time
    schedules = query.order_by(Schedule.schedule_date, Schedule.schedule_time).all()
    
    # Group schedules by date for the template
    schedules_by_date = {}
    for schedule in schedules:
        date_str = schedule.schedule_date.strftime('%Y-%m-%d')
        if date_str not in schedules_by_date:
            schedules_by_date[date_str] = []
        schedules_by_date[date_str].append(schedule)
    
    return render_template('admin/schedules.html', 
                         schedules_by_date=schedules_by_date,
                         start_date=start_date,
                         end_date=end_date,
                         datetime=datetime)

@app.route('/admin/requests')
@login_required
def schedule_requests():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    # Get pending schedules (you might want to add a status field to Schedule model)
    pending_schedules = Schedule.query.join(User).order_by(Schedule.created_at.desc()).all()
    return render_template('admin/requests.html', schedules=pending_schedules)

@app.route('/admin/schedule/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def manage_schedule(schedule_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    schedule = Schedule.query.get_or_404(schedule_id)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'approve':
            schedule.status = 'approved'
            db.session.commit()
            flash('Schedule approved successfully!')
        elif action == 'reject':
            schedule.status = 'rejected'
            db.session.commit()
            flash('Schedule rejected!')
        
        return redirect(url_for('schedule_requests'))
    
    return render_template('admin/schedule_detail.html', schedule=schedule)

@app.route('/api/schedule/<int:schedule_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_schedule_status(schedule_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    schedule = Schedule.query.get_or_404(schedule_id)
    data = request.get_json()
    action = data.get('action')
    
    if action in ['approve', 'reject']:
        try:
            schedule.status = 'approved' if action == 'approve' else 'rejected'
            schedule.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({
                'status': 'success',
                'message': f'Schedule {action}d successfully',
                'new_status': schedule.status,
                'success': True
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'error': 'Invalid action', 'success': False}), 400

@app.route('/admin/reports')
@login_required
def reports():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    # Get monthly statistics
    monthly_stats = []
    current_month = datetime.now().month
    for month in range(1, 13):
        total = Schedule.query.filter(db.extract('month', Schedule.schedule_date) == month).count()
        month_name = datetime(2024, month, 1).strftime('%B')
        monthly_stats.append({'month': month_name, 'total': total})
    
    # Get health declaration statistics
    health_stats = {
        'fever_count': HealthDeclaration.query.filter_by(has_fever=True).count(),
        'cough_count': HealthDeclaration.query.filter_by(has_cough=True).count(),
        'cold_count': HealthDeclaration.query.filter_by(has_cold=True).count()
    }
    
    return render_template('admin/reports.html', monthly_stats=monthly_stats, health_stats=health_stats)

@app.route('/api/check-schedule-availability', methods=['POST'])
@login_required
def check_schedule_availability():
    data = request.get_json()
    date_str = data.get('date')
    
    try:
        schedule_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        # Count approved and pending schedules for the date
        total_schedules = Schedule.query.filter(
            Schedule.schedule_date == schedule_date,
            Schedule.status.in_(['approved', 'pending'])
        ).count()
        
        available_slots = 30 - total_schedules
        return jsonify({
            'available': available_slots > 0,
            'remaining_slots': max(0, available_slots),
            'message': f'{available_slots} slots available' if available_slots > 0 else 'No slots available for this date'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/schedule/<int:schedule_id>/health-declaration')
@login_required
def get_health_declaration(schedule_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    schedule = Schedule.query.get_or_404(schedule_id)
    if not schedule.health_declaration:
        return jsonify({'error': 'No health declaration found'}), 404
    
    return jsonify({
        'has_fever': schedule.health_declaration.has_fever,
        'has_cough': schedule.health_declaration.has_cough,
        'has_cold': schedule.health_declaration.has_cold,
        'has_sore_throat': schedule.health_declaration.has_sore_throat,
        'has_breathing_problems': schedule.health_declaration.has_breathing_problems,
        'has_diarrhea': schedule.health_declaration.has_diarrhea,
        'has_body_pains': schedule.health_declaration.has_body_pains,
        'has_travelled': schedule.health_declaration.has_travelled,
        'has_contact_with_covid': schedule.health_declaration.has_contact_with_covid
    })

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json()
    
    try:
        # Check if email is being changed and if it's already taken
        if data['email'] != current_user.email and User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        current_user.name = data['name']
        current_user.email = data['email']
        
        if data.get('password'):
            current_user.set_password(data['password'])
        
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/schedule-history')
@login_required
@admin_required
def schedule_history():
    # Get all processed schedules (approved or rejected)
    processed_schedules = Schedule.query.filter(
        Schedule.status.in_(['approved', 'rejected'])
    ).order_by(Schedule.updated_at.desc()).all()
    
    return render_template('admin/schedule_history.html', schedules=processed_schedules)

@app.route('/api/pending-count')
@login_required
@admin_required
def get_pending_count():
    count = Schedule.query.filter_by(status='pending').count()
    return jsonify({'count': count})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 