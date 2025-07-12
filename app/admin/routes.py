from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_babel import gettext as _
from datetime import datetime, timedelta
from sqlalchemy import func
import functools
import platform
import flask
import sqlalchemy

from app.admin import bp
from app.admin.forms import UserApprovalForm, UserRoleForm, SubscriptionStatusForm, AdminNoteForm
from app.models import User, Subscription, ExcelFile, ChatSession, ChatMessage, UserRole, SubscriptionStatus
from app import db

def admin_required(f):
    """Decorator to require admin role"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash(_('Access denied. Admin privileges required.'), 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get statistics
    total_users = User.query.count()
    pending_approvals = User.query.filter_by(is_approved=False).count()
    active_subscriptions = Subscription.query.filter_by(status=SubscriptionStatus.ACTIVE).count()
    total_files = ExcelFile.query.filter_by(is_active=True).count()
    
    # Recent registrations
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Pending approvals
    pending_users = User.query.filter_by(is_approved=False).order_by(User.created_at.desc()).limit(10).all()
    
    # Subscription statistics
    subscription_stats = db.session.query(
        Subscription.plan_type,
        func.count(Subscription.id).label('count')
    ).filter_by(status=SubscriptionStatus.ACTIVE).group_by(Subscription.plan_type).all()
    
    return render_template('admin/dashboard.html',
                         title=_('Admin Dashboard'),
                         total_users=total_users,
                         pending_approvals=pending_approvals,
                         active_subscriptions=active_subscriptions,
                         total_files=total_files,
                         recent_users=recent_users,
                         pending_users=pending_users,
                         subscription_stats=subscription_stats)

@bp.route('/users')
@login_required
@admin_required
def users():
    """User management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filter options
    role_filter = request.args.get('role')
    approval_filter = request.args.get('approval')
    search = request.args.get('search', '').strip()
    
    query = User.query
    
    if role_filter:
        query = query.filter_by(role=UserRole(role_filter))
    
    if approval_filter == 'approved':
        query = query.filter_by(is_approved=True)
    elif approval_filter == 'pending':
        query = query.filter_by(is_approved=False)
    
    if search:
        query = query.filter(
            db.or_(
                User.email.contains(search),
                User.first_name.contains(search),
                User.last_name.contains(search)
            )
        )
    
    users_pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html',
                         title=_('User Management'),
                         users=users_pagination.items,
                         pagination=users_pagination,
                         role_filter=role_filter,
                         approval_filter=approval_filter,
                         search=search)

@bp.route('/user/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """User detail page"""
    user = User.query.get_or_404(user_id)
    
    # Get user's files and sessions
    files = user.excel_files.filter_by(is_active=True).all()
    sessions = user.chat_sessions.filter_by(is_active=True).order_by(ChatSession.last_activity.desc()).all()
    
    return render_template('admin/user_detail.html',
                         title=_('User Details'),
                         user=user,
                         files=files,
                         sessions=sessions)

@bp.route('/user/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    """Approve or disapprove user"""
    user = User.query.get_or_404(user_id)
    
    approve = request.json.get('approve', False)
    user.is_approved = approve
    
    db.session.commit()
    
    action = _('approved') if approve else _('disapproved')
    flash(_('User %(email)s has been %(action)s.', email=user.email, action=action), 'success')
    
    return jsonify({'status': 'success', 'approved': approve})

@bp.route('/user/<int:user_id>/role', methods=['GET', 'POST'])
@login_required
@admin_required
def update_user_role(user_id):
    """Update user role"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash(_('You cannot change your own role.'), 'error')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    form = UserRoleForm(obj=user)
    
    if form.validate_on_submit():
        old_role = user.role.value
        user.role = UserRole(form.role.data)
        
        db.session.commit()
        
        flash(_('User role updated from %(old_role)s to %(new_role)s.', 
                old_role=old_role, new_role=user.role.value), 'success')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    return render_template('admin/update_user_role.html',
                         title=_('Update User Role'),
                         form=form,
                         user=user)

@bp.route('/subscriptions')
@login_required
@admin_required
def subscriptions():
    """Subscription management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filter options
    status_filter = request.args.get('status')
    plan_filter = request.args.get('plan')
    
    query = Subscription.query.join(User)
    
    if status_filter:
        query = query.filter(Subscription.status == SubscriptionStatus(status_filter))
    
    if plan_filter:
        query = query.filter(Subscription.plan_type == PlanType(plan_filter))
    
    subscriptions_pagination = query.order_by(Subscription.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/subscriptions.html',
                         title=_('Subscription Management'),
                         subscriptions=subscriptions_pagination.items,
                         pagination=subscriptions_pagination,
                         status_filter=status_filter,
                         plan_filter=plan_filter)

@bp.route('/subscription/<int:subscription_id>')
@login_required
@admin_required
def subscription_detail(subscription_id):
    """Subscription detail page"""
    subscription = Subscription.query.get_or_404(subscription_id)
    
    return render_template('admin/subscription_detail.html',
                         title=_('Subscription Details'),
                         subscription=subscription)

@bp.route('/subscription/<int:subscription_id>/status', methods=['GET', 'POST'])
@login_required
@admin_required
def update_subscription_status(subscription_id):
    """Update subscription status"""
    subscription = Subscription.query.get_or_404(subscription_id)
    
    form = SubscriptionStatusForm(obj=subscription)
    
    if form.validate_on_submit():
        old_status = subscription.status.value
        subscription.status = SubscriptionStatus(form.status.data)
        
        db.session.commit()
        
        flash(_('Subscription status updated from %(old_status)s to %(new_status)s.', 
                old_status=old_status, new_status=subscription.status.value), 'success')
        return redirect(url_for('admin.subscription_detail', subscription_id=subscription_id))
    
    return render_template('admin/update_subscription_status.html',
                         title=_('Update Subscription Status'),
                         form=form,
                         subscription=subscription)

@bp.route('/files')
@login_required
@admin_required
def files():
    """File management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = ExcelFile.query.join(User).filter(ExcelFile.is_active == True)
    
    files_pagination = query.order_by(ExcelFile.upload_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Calculate total storage usage
    total_storage = db.session.query(func.sum(ExcelFile.file_size)).filter_by(is_active=True).scalar() or 0
    total_storage_mb = round(total_storage / (1024 * 1024), 2)
    
    return render_template('admin/files.html',
                         title=_('File Management'),
                         files=files_pagination.items,
                         pagination=files_pagination,
                         total_storage_mb=total_storage_mb)

@bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Analytics and reporting"""
    # User statistics
    user_stats = {
        'total': User.query.count(),
        'approved': User.query.filter_by(is_approved=True).count(),
        'pending': User.query.filter_by(is_approved=False).count(),
        'admins': User.query.filter_by(role=UserRole.ADMIN).count()
    }
    
    # Subscription statistics
    subscription_stats = {
        'active': Subscription.query.filter_by(status=SubscriptionStatus.ACTIVE).count(),
        'inactive': Subscription.query.filter_by(status=SubscriptionStatus.INACTIVE).count(),
        'cancelled': Subscription.query.filter_by(status=SubscriptionStatus.CANCELLED).count(),
        'past_due': Subscription.query.filter_by(status=SubscriptionStatus.PAST_DUE).count()
    }
    
    # Plan distribution
    plan_stats = db.session.query(
        Subscription.plan_type,
        func.count(Subscription.id).label('count')
    ).group_by(Subscription.plan_type).all()
    
    # File statistics
    file_stats = {
        'total': ExcelFile.query.filter_by(is_active=True).count(),
        'total_size': db.session.query(func.sum(ExcelFile.file_size)).filter_by(is_active=True).scalar() or 0
    }
    file_stats['total_size_mb'] = round(file_stats['total_size'] / (1024 * 1024), 2)
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_files = ExcelFile.query.filter_by(is_active=True).order_by(ExcelFile.upload_date.desc()).limit(10).all()
    
    # Registration trends (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_registrations = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(User.created_at >= thirty_days_ago).group_by(func.date(User.created_at)).all()
    
    return render_template('admin/analytics.html',
                         title=_('Analytics'),
                         user_stats=user_stats,
                         subscription_stats=subscription_stats,
                         plan_stats=plan_stats,
                         file_stats=file_stats,
                         recent_users=recent_users,
                         recent_files=recent_files,
                         daily_registrations=daily_registrations)

@bp.route('/logs')
@login_required
@admin_required
def logs():
    """System logs (placeholder for future implementation)"""
    log_type = request.args.get('log_type')
    return render_template('admin/logs.html', title=_('System Logs'), log_type=log_type)

@bp.route('/description')
@login_required
@admin_required
def description():
    """System description and help page"""
    return render_template('admin/description.html', title=_('System Description'))

@bp.route('/system')
@login_required
@admin_required
def system():
    """System settings and configuration"""
    # Получаем информацию о системе
    system_info = {
        'python_version': platform.python_version(),
        'flask_version': flask.__version__,
        'sqlalchemy_version': sqlalchemy.__version__,
        'database_url': current_app.config.get('DATABASE_URL', 'Not configured'),
        'upload_folder': current_app.config.get('UPLOAD_FOLDER', 'Not configured'),
        'max_content_length': current_app.config.get('MAX_CONTENT_LENGTH', 0) // (1024 * 1024),
        'env': current_app.config.get('ENV', 'production'),
        'debug': current_app.config.get('DEBUG', False),
        'secret_key': 'Configured' if current_app.config.get('SECRET_KEY') else 'Not configured',
        'stripe_configured': bool(current_app.config.get('STRIPE_SECRET_KEY')),
        'openai_configured': bool(current_app.config.get('OPENAI_API_KEY'))
    }
    
    return render_template('admin/system.html', title=_('System Settings'), system_info=system_info)

@bp.route('/file/<int:file_id>/toggle-status', methods=['GET', 'POST'])
@login_required
@admin_required
def toggle_file_status(file_id):
    """Toggle file active status"""
    excel_file = ExcelFile.query.get_or_404(file_id)
    
    # Get desired state from request
    make_active = request.args.get('active', '0') == '1'
    
    # Update file status
    excel_file.is_active = make_active
    db.session.commit()
    
    flash(_('File status updated successfully.'), 'success')
    return redirect(url_for('admin.files'))
