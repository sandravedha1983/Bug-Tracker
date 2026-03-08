import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import current_user
from werkzeug.security import check_password_hash
from functools import wraps
from .models import db, User, Bug
from datetime import datetime, timedelta
from .email_utils import send_verification_email, generate_verification_token
from .analytics_utils import (
    get_priority_distribution, 
    get_status_overview, 
    get_trends_data, 
    get_developer_load
)

admin_bp = Blueprint('platform_admin', __name__, url_prefix='/platform-admin')

def admin_session_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow either custom admin session OR valid flask-login session with admin role
        is_admin_session = session.get("admin_authenticated")
        is_flask_admin = current_user.is_authenticated and current_user.role == 'admin'
        
        if not is_admin_session and not is_flask_admin:
            flash("Admin authentication required.", "warning")
            return redirect(url_for('platform_admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get("admin_authenticated"):
        return redirect(url_for('platform_admin.dashboard'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        admin_hash = current_app.config.get('ADMIN_PASSWORD_HASH') or os.environ.get('ADMIN_PASSWORD_HASH')
        
        if admin_hash and check_password_hash(admin_hash, password):
            session["admin_authenticated"] = True
            flash("Admin session started.", "success")
            return redirect(url_for('platform_admin.dashboard'))
        else:
            flash("Invalid admin password", "danger")
            
    return render_template('platform_admin/login.html')

@admin_bp.route('/logout')
def logout():
    session.pop("admin_authenticated", None)
    flash("Admin session ended.", "info")
    return redirect(url_for('platform_admin.login'))

@admin_bp.route('/')
@admin_session_required
def dashboard():
    online_threshold = datetime.utcnow() - timedelta(minutes=5)
    stats = {
        'total_users': User.query.count(),
        'unverified_users': User.query.filter_by(is_verified=False).count(),
        'suspended_users': User.query.filter_by(is_suspended=True).count(),
        'online_devs': User.query.filter(User.role == 'developer', User.last_active_at >= online_threshold).count(),
        'total_bugs': Bug.query.count(),
        'unassigned_bugs': Bug.query.filter_by(assigned_to=None).count()
    }
    return render_template('platform_admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
@admin_session_required
def users():
    users_list = User.query.all()
    now = datetime.utcnow()
    return render_template('platform_admin/users.html', users=users_list, now=now)

@admin_bp.route('/user/delete/<int:user_id>', methods=['POST'])
@admin_session_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.email} deleted.", "success")
    return redirect(url_for('platform_admin.users'))

@admin_bp.route('/user/suspend/<int:user_id>', methods=['POST'])
@admin_session_required
def toggle_suspend(user_id):
    user = User.query.get_or_404(user_id)
    user.is_suspended = not user.is_suspended
    db.session.commit()
    status = "suspended" if user.is_suspended else "unsuspended"
    flash(f"User {user.email} {status}.", "info")
    return redirect(url_for('platform_admin.users'))

@admin_bp.route('/user/role/<int:user_id>', methods=['POST'])
@admin_session_required
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ['admin', 'developer', 'tester']:
        user.role = new_role
        db.session.commit()
        flash(f"Role updated for {user.email}.", "success")
    return redirect(url_for('platform_admin.users'))

@admin_bp.route('/developers')
@admin_session_required
def developers():
    devs = User.query.filter_by(role='developer').all()
    now = datetime.utcnow()
    # Add workload info
    for dev in devs:
        dev.workload = Bug.query.filter_by(assigned_to=dev.id, status='Open').count()
        dev.current_bug = Bug.query.filter_by(assigned_to=dev.id, status='In Progress').first()
    return render_template('platform_admin/developers.html', devs=devs, now=now)

@admin_bp.route('/bug-assignment')
@admin_session_required
def bug_assignment():
    unassigned_bugs = Bug.query.filter_by(assigned_to=None).all()
    devs = User.query.filter_by(role='developer').all()
    now = datetime.utcnow()
    online_threshold = now - timedelta(minutes=5)
    
    # Suggestion logic
    suggestions = {}
    for bug in unassigned_bugs:
        # Rule 1: Prefer online developers
        online_devs = [d for d in devs if d.last_active_at >= online_threshold]
        if online_devs:
            # Rule 2: Least active bugs
            suggested = min(online_devs, key=lambda d: Bug.query.filter_by(assigned_to=d.id, status='Open').count())
        else:
            # Rule 3: Lowest workload (offline)
            suggested = min(devs, key=lambda d: Bug.query.filter_by(assigned_to=d.id, status='Open').count()) if devs else None
        suggestions[bug.id] = suggested

    return render_template('platform_admin/bug_assignment.html', bugs=unassigned_bugs, devs=devs, suggestions=suggestions, now=now)

@admin_bp.route('/email-management')
@admin_session_required
def email_management():
    users_list = User.query.all()
    return render_template('platform_admin/email_management.html', users=users_list)

@admin_bp.route('/email/verify/<int:user_id>', methods=['POST'])
@admin_session_required
def manual_verify(user_id):
    user = User.query.get_or_404(user_id)
    user.is_verified = True
    db.session.commit()
    flash(f"User {user.email} manually verified.", "success")
    return redirect(url_for('platform_admin.email_management'))

@admin_bp.route('/email/resend/<int:user_id>', methods=['POST'])
@admin_session_required
def resend_verification(user_id):
    user = User.query.get_or_404(user_id)
    # Use current_app secret key
    token = generate_verification_token(user.email, current_app.config['SECRET_KEY'])
    if send_verification_email(user.email, token):
        flash(f"Verification email resent to {user.email}.", "success")
    else:
        flash("Failed to send email.", "danger")
    return redirect(url_for('platform_admin.email_management'))

@admin_bp.route('/database')
@admin_session_required
def database():
    target = request.args.get('table', 'users')
    if target == 'bugs':
        data = Bug.query.all()
        cols = ['id', 'title', 'priority', 'status', 'assigned_to']
    else:
        data = User.query.all()
        cols = ['id', 'name', 'email', 'role', 'is_verified']
    return render_template('platform_admin/database.html', data=data, cols=cols, table=target)

@admin_bp.route('/database/delete-bug/<int:bug_id>', methods=['POST'])
@admin_session_required
def delete_bug(bug_id):
    bug = Bug.query.get_or_404(bug_id)
    db.session.delete(bug)
    db.session.commit()
    flash("Bug deleted from database.", "info")
    return redirect(url_for('platform_admin.database', table='bugs'))

# --- Analytics API (Protected by Admin Session) ---

@admin_bp.route('/api/stats/priority')
@admin_session_required
def api_priority():
    """
    Admin: Priority Distribution
    ---
    tags:
      - Admin
    responses:
      200:
        description: Priority stats for admin
    """
    return jsonify(get_priority_distribution())

@admin_bp.route('/api/stats/status')
@admin_session_required
def api_status():
    """
    Admin: Status Metrics
    ---
    tags:
      - Admin
    responses:
      200:
        description: Status metrics for admin
    """
    return jsonify(get_status_overview())

@admin_bp.route('/api/stats/trends')
@admin_session_required
def api_trends():
    """
    Admin: Trends Analytics
    ---
    tags:
      - Admin
    responses:
      200:
        description: Trends data for admin
    """
    return jsonify(get_trends_data())

@admin_bp.route('/api/stats/developer-load')
@admin_session_required
def api_dev_load():
    """
    Admin: Developer Workload
    ---
    tags:
      - Admin
    responses:
      200:
        description: Developer load stats for admin
    """
    return jsonify(get_developer_load())

@admin_bp.route('/bug/assign/<int:bug_id>', methods=['POST'])
@admin_session_required
def assign_bug(bug_id):
    bug = Bug.query.get_or_404(bug_id)
    dev_id = request.form.get('developer_id')
    bug.assigned_to = dev_id
    db.session.commit()
    flash('Bug assigned successfully', 'success')
    return redirect(request.referrer or url_for('platform_admin.bug_assignment'))

@admin_bp.route('/bug/auto-assign-dev/<int:bug_id>', methods=['POST'])
@admin_session_required
def auto_assign_dev_action(bug_id):
    bug = Bug.query.get_or_404(bug_id)
    
    # Get all developers
    devs = User.query.filter_by(role='developer').all()
    if not devs:
        flash('No developers available to assign this bug.', 'danger')
        return redirect(url_for('platform_admin.bug_assignment'))
        
    now = datetime.utcnow()
    online_threshold = now - timedelta(minutes=5)
    
    # Filter online developers
    online_devs = [d for d in devs if d.last_active_at >= online_threshold]
    
    target_pool = online_devs if online_devs else devs
    
    # Select dev with lowest workload
    suggested_dev = min(target_pool, key=lambda d: Bug.query.filter_by(assigned_to=d.id).filter(Bug.status.in_(['Open', 'In Progress'])).count())
    
    # Assign
    bug.assigned_to = suggested_dev.id
    db.session.commit()
    
    flash(f'Bug successfully assigned to {suggested_dev.name}', 'success')
    return redirect(url_for('platform_admin.bug_assignment'))

