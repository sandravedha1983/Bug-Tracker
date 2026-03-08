import os
import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User, Bug
from .ai_utils import predict_priority, generate_summary
from .email_utils import generate_verification_token, confirm_verification_token, send_verification_email
from .decorators import role_required, admin_required, developer_required, tester_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('home.html')

@main_bp.before_app_request
def update_last_active():
    if current_user.is_authenticated:
        current_user.last_active_at = datetime.utcnow()
        db.session.commit()

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                if user.is_suspended:
                    flash('Your account has been suspended. Please contact support.', 'danger')
                    return redirect(url_for('main.login'))
                if not user.is_verified:
                    flash('Please verify your email before logging in.', 'warning')
                    return redirect(url_for('main.login'))
                login_user(user)
                return redirect(url_for('main.dashboard'))
            else:
                flash('Invalid email or password', 'danger')
        except Exception as e:
            current_app.logger.error(f"Login database error: {str(e)}")
            flash('A database error occurred. Please try again later.', 'danger')
            
    return render_template('login.html')

@main_bp.route('/api/login', methods=['POST'])
def api_login():
    """
    User Login API
    ---
    tags:
      - Authentication
    parameters:
      - name: email
        in: formData
        type: string
        required: true
      - name: password
        in: formData
        type: string
        required: true
    responses:
      200:
        description: Login successful
        schema:
          properties:
            token:
              type: string
              example: "user_session_token"
      401:
        description: Invalid credentials
    """
    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        return jsonify({"token": "mock_token_for_docs"}), 200
    return jsonify({"message": "Invalid credentials"}), 401

@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'tester')

        email_regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$'
        if not re.match(email_regex, email):
            flash('Invalid email format.', 'danger')
            return redirect(url_for('main.signup'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('main.signup'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('main.signup'))

        new_user = User(name=name, email=email, role=role, is_verified=False)
        new_user.set_password(password)
        
        token = generate_verification_token(email, current_app.config['SECRET_KEY'])
        new_user.verification_token = token
        
        db.session.add(new_user)
        db.session.commit()
        
        if send_verification_email(email, token):
            flash('Signup successful! Please check your email to verify your account.', 'success')
        else:
            flash('Signup successful, but the verification email could not be sent. Please contact support.', 'warning')
            
        return redirect(url_for('main.login'))

    return render_template('signup.html')

@main_bp.route('/api/signup', methods=['POST'])
def api_signup():
    """
    User Signup API
    ---
    tags:
      - Authentication
    parameters:
      - name: name
        in: formData
        type: string
        required: true
      - name: email
        in: formData
        type: string
        required: true
      - name: password
        in: formData
        type: string
        required: true
    responses:
      201:
        description: Signup successful
        schema:
          properties:
            message:
              type: string
              example: "Signup successful"
      400:
        description: Invalid input
    """
    return jsonify({"message": "Signup successful"}), 201

@main_bp.route('/verify-email/<token>')
def verify_email(token):
    email = confirm_verification_token(token, current_app.config['SECRET_KEY'])
    if not email:
        flash('The verification link is invalid or has expired. You can request a new one.', 'danger')
        return redirect(url_for('main.login'))
    
    user = User.query.filter_by(email=email).first_or_404()
    if user.is_verified:
        flash('Account already verified. Please login.', 'info')
    else:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        flash('Your account has been verified! You can now login.', 'success')
        return render_template('verify_success.html')
    
    return redirect(url_for('main.login'))

@main_bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification_request():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            if user.is_verified:
                flash('Your account is already verified.', 'info')
            else:
                token = generate_verification_token(email, current_app.config['SECRET_KEY'])
                if send_verification_email(email, token):
                    flash('A new verification email has been sent.', 'success')
                else:
                    flash('Failed to send verification email. Please try again later.', 'danger')
        else:
            flash('Email not found.', 'danger')
        return redirect(url_for('main.login'))
    return render_template('resend_verification.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'total': Bug.query.count(),
        'open': Bug.query.filter_by(status='Open').count(),
        'high_priority': Bug.query.filter_by(priority='High').count(),
        'closed': Bug.query.filter_by(status='Closed').count()
    }
    
    if current_user.role == 'admin':
        bugs = Bug.query.order_by(Bug.created_at.desc()).limit(5).all()
    elif current_user.role == 'developer':
        bugs = Bug.query.filter_by(assigned_to=current_user.id).order_by(Bug.created_at.desc()).limit(5).all()
    else: # tester
        bugs = Bug.query.filter_by(created_by=current_user.id).order_by(Bug.created_at.desc()).limit(5).all()
        
    return render_template('dashboard.html', stats=stats, recent_bugs=bugs)

@main_bp.route('/bugs')
@login_required
def bugs():
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    search_query = request.args.get('search')
    
    query = Bug.query
    
    if current_user.role == 'developer':
        query = query.filter_by(assigned_to=current_user.id)
    elif current_user.role == 'tester':
        query = query.filter_by(created_by=current_user.id)
        
    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if search_query:
        query = query.filter(Bug.title.contains(search_query) | Bug.description.contains(search_query))
        
    bugs_list = query.order_by(Bug.created_at.desc()).all()
    developers = User.query.filter_by(role='developer').all()
    
    return render_template('bugs.html', bugs=bugs_list, developers=developers)

@main_bp.route('/api/bugs', methods=['GET'])
@login_required
def api_get_bugs():
    """
    Get All Bugs
    ---
    tags:
      - Bug Management
    responses:
      200:
        description: A list of bugs
        schema:
          type: array
          items:
            properties:
              id:
                type: integer
              title:
                type: string
              priority:
                type: string
              status:
                type: string
    """
    bugs = Bug.query.all()
    return jsonify([bug.to_dict() for bug in bugs])

@main_bp.route('/api/bugs', methods=['POST'])
@login_required
def api_add_bug():
    """
    Create a New Bug
    ---
    tags:
      - Bug Management
    parameters:
      - name: title
        in: formData
        type: string
        required: true
      - name: description
        in: formData
        type: string
        required: true
      - name: priority
        in: formData
        type: string
    responses:
      201:
        description: Bug created successfully
    """
    return jsonify({"message": "Bug created successfully"}), 201

@main_bp.route('/bug/add', methods=['POST'])
@login_required
@tester_required
def add_bug():
    title = request.form.get('title')
    description = request.form.get('description')
    github_url = request.form.get('github_url')
    
    try:
        priority = predict_priority(description)
        ai_summary = generate_summary(description)
    except Exception as e:
        print(f"AI Error: {e}")
        priority = "Medium"
        ai_summary = description[:100]

    new_bug = Bug(
        title=title,
        description=description,
        priority=priority,
        ai_summary=ai_summary,
        created_by=current_user.id,
        github_url=github_url
    )
    
    db.session.add(new_bug)
    db.session.commit()
    
    flash(f'Bug reported successfully! AI suggested priority: {priority}', 'success')
    return redirect(url_for('main.bugs'))

@main_bp.route('/api/bugs/<int:bug_id>', methods=['PUT'])
@login_required
def api_update_bug(bug_id):
    """
    Update Bug Status
    ---
    tags:
      - Bug Management
    parameters:
      - name: bug_id
        in: path
        type: integer
        required: true
      - name: status
        in: formData
        type: string
        required: true
        enum: [Open, In Progress, Resolved, Closed]
    responses:
      200:
        description: Bug status updated successfully
      404:
        description: Bug not found
    """
    bug = Bug.query.get_or_404(bug_id)
    if current_user.role == 'developer' and bug.assigned_to != current_user.id:
        return jsonify({"message": "Permission denied"}), 403
    
    new_status = request.form.get('status')
    if new_status:
        bug.status = new_status
        db.session.commit()
        return jsonify({"message": f"Status updated to {new_status}"}), 200
    return jsonify({"message": "No status provided"}), 400

@main_bp.route('/bug/assign/<int:bug_id>', methods=['POST'])
@login_required
@admin_required
def assign_bug(bug_id):
    bug = Bug.query.get_or_404(bug_id)
    dev_id = request.form.get('developer_id')
    bug.assigned_to = dev_id
    db.session.commit()
    flash('Bug assigned successfully', 'success')
    return redirect(url_for('main.bugs'))


@main_bp.route('/bug/status/<int:bug_id>', methods=['POST'])
@login_required
def update_status(bug_id):
    bug = Bug.query.get_or_404(bug_id)
    
    if current_user.role == 'developer' and bug.assigned_to != current_user.id:
        flash('Permission denied', 'danger')
        return redirect(url_for('main.bugs'))
    
    new_status = request.form.get('status')
    bug.status = new_status
    db.session.commit()
    flash(f'Status updated to {new_status}', 'success')
    return redirect(url_for('main.bugs'))

@main_bp.route('/init-db')
def init_db():
    """Manual trigger to create database tables (useful for Vercel/Serverless)"""
    try:
        db.create_all()
        return "Database tables verified/created successfully.", 200
    except Exception as e:
        return f"Database initialization failed: {str(e)}", 500

@main_bp.route('/bug/delete/<int:bug_id>', methods=['POST'])
@login_required
@admin_required
def delete_bug(bug_id):
    bug = Bug.query.get_or_404(bug_id)
    db.session.delete(bug)
    db.session.commit()
    flash('Bug deleted', 'info')
    return redirect(url_for('main.bugs'))
