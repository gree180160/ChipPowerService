from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user
from app.models.user import User
from app.models.session import Session
from app import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))

        if user.status != 'active':
            flash('Your account is not active', 'warning')
            return redirect(url_for('auth.login'))

        # Update last login
        user.last_login = db.func.current_timestamp()
        db.session.commit()

        # Create session
        session = Session.create_session(
            user_id=user.user_id,
            token=user.get_auth_token(),
            ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(session)
        db.session.commit()

        login_user(user, remember=remember)
        flash('Login successful', 'success')
        return redirect(url_for('home'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        # Invalidate session
        Session.query.filter_by(user_id=current_user.user_id).delete()
        db.session.commit()

    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))