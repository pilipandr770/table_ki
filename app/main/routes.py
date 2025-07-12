from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, send_file, session
from flask_login import login_required, current_user
from flask_babel import gettext as _, get_locale
import os
import json
from datetime import datetime

from app.main import bp
from app.main.forms import FileUploadForm, ChatForm, NewChatSessionForm, EditFilePermissionForm
from app.main.utils import save_uploaded_file, load_excel_data, save_excel_data, get_excel_summary, delete_file
from app.models import User, ExcelFile, ChatSession, ChatMessage, PermissionMode, MessageType
from app import db

@bp.route('/')
def index():
    """Home page"""
    return render_template('main/index.html', title=_('Welcome'))

@bp.route('/voice_test')
@login_required
def voice_test():
    """Test page for voice functionality"""
    return render_template('main/voice_test.html', title=_('Voice Test'))

@bp.route('/chat/<int:session_id>/voice')
@login_required
def voice_message(session_id):
    """Voice message page for a specific chat session"""
    chat_session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    return render_template('main/voice_message.html', 
                          title=_('Voice Message'),
                          session_id=session_id)

@bp.route('/status')
def status():
    """Development status page"""
    status_info = {
        'debug_mode': current_app.debug,
        'bypass_stripe': current_app.config.get('BYPASS_STRIPE', False),
        'bypass_openai': current_app.config.get('BYPASS_OPENAI', False),
        'stripe_configured': bool(current_app.config.get('STRIPE_SECRET_KEY') and 
                                not current_app.config.get('STRIPE_SECRET_KEY').startswith('sk_test_your')),
        'openai_configured': bool(current_app.config.get('OPENAI_API_KEY') and 
                                current_app.config.get('OPENAI_API_KEY') != 'your-openai-api-key'),
        'database_configured': bool(current_app.config.get('DATABASE_URL')),
        'mail_configured': bool(current_app.config.get('MAIL_SERVER') and 
                              current_app.config.get('MAIL_USERNAME'))
    }
    return render_template('main/status.html', title=_('Application Status'), status=status_info)

@bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    if not current_user.can_access_system() and not current_user.is_admin():
        flash(_('Your account is pending admin approval or needs an active subscription.'), 'warning')
        return redirect(url_for('main.index'))
    
    # Get user's files
    files = current_user.excel_files.filter_by(is_active=True).all()
    
    # Get recent chat sessions
    recent_sessions = current_user.chat_sessions.filter_by(is_active=True)\
                                                .order_by(ChatSession.last_activity.desc())\
                                                .limit(5).all()
    
    # Check upload limits
    can_upload, remaining_uploads = current_user.can_upload_files()
    
    return render_template('main/dashboard.html', 
                         title=_('Dashboard'),
                         files=files,
                         recent_sessions=recent_sessions,
                         can_upload=can_upload,
                         remaining_uploads=remaining_uploads)

@bp.route('/files')
@login_required
def files():
    """File management page"""
    if not current_user.can_access_system():
        flash(_('Access denied.'), 'error')
        return redirect(url_for('main.index'))
    
    files = current_user.excel_files.filter_by(is_active=True).all()
    can_upload, remaining_uploads = current_user.can_upload_files()
    
    return render_template('main/files.html',
                         title=_('My Files'),
                         files=files,
                         can_upload=can_upload,
                         remaining_uploads=remaining_uploads,
                         subscription=current_user.subscription)

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """File upload page"""
    if not current_user.can_access_system():
        flash(_('Access denied.'), 'error')
        return redirect(url_for('main.index'))
    
    can_upload, remaining_uploads = current_user.can_upload_files()
    if not can_upload:
        flash(_('You have reached your file upload limit for your subscription plan.'), 'error')
        return redirect(url_for('main.files'))
    
    form = FileUploadForm()
    
    if form.validate_on_submit():
        file_info, error = save_uploaded_file(form.file.data, current_user.id)
        
        if error:
            flash(_(error), 'error')
        else:
            # Save file record to database
            excel_file = ExcelFile(
                user_id=current_user.id,
                filename=file_info['filename'],
                original_filename=file_info['original_filename'],
                file_path=file_info['file_path'],
                file_size=file_info['file_size'],
                permission_mode=PermissionMode(form.permission_mode.data),
                sheet_names=file_info['sheet_names'],
                row_count=file_info['row_count'],
                column_count=file_info['column_count']
            )
            
            db.session.add(excel_file)
            db.session.commit()
            
            flash(_('File uploaded successfully!'), 'success')
            return redirect(url_for('main.files'))
    
    # Получить информацию о плане подписки
    plan_info = None
    if current_user.subscription:
        if current_user.subscription.plan_type.value == 'single-table':
            plan_info = {'name': _('Single Table Plan'), 'max_files': 1}
        elif current_user.subscription.plan_type.value == 'multi-table':
            plan_info = {'name': _('Multi Table Plan'), 'max_files': 10}
    
    return render_template('main/upload.html',
                         title=_('Upload File'),
                         form=form,
                         remaining_uploads=remaining_uploads,
                         plan_info=plan_info)

@bp.route('/file/<int:file_id>')
@login_required
def view_file(file_id):
    """View file details and data"""
    excel_file = ExcelFile.query.filter_by(id=file_id, user_id=current_user.id, is_active=True).first_or_404()
    
    if not excel_file.can_read():
        flash(_('You do not have permission to view this file.'), 'error')
        return redirect(url_for('main.files'))
    
    # Load Excel data
    sheet_name = request.args.get('sheet')
    data, error = load_excel_data(excel_file.file_path, sheet_name)
    
    if error:
        flash(_(error), 'error')
        data = None
    
    # Get sheet names
    sheet_names = json.loads(excel_file.sheet_names) if excel_file.sheet_names else []
    
    # Используем редактируемый шаблон с возможностью изменения таблицы
    return render_template('main/view_file_editable.html',
                         title=_('View File'),
                         excel_file=excel_file,
                         data=data,
                         sheet_names=sheet_names,
                         current_sheet=sheet_name)

@bp.route('/file/<int:file_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_file(file_id):
    """Edit file permissions"""
    excel_file = ExcelFile.query.filter_by(id=file_id, user_id=current_user.id, is_active=True).first_or_404()
    
    form = EditFilePermissionForm(obj=excel_file)
    
    if form.validate_on_submit():
        excel_file.permission_mode = PermissionMode(form.permission_mode.data)
        db.session.commit()
        flash(_('File permissions updated successfully.'), 'success')
        return redirect(url_for('main.view_file', file_id=file_id))
    
    return render_template('main/edit_file.html',
                         title=_('Edit File'),
                         form=form,
                         excel_file=excel_file)

@bp.route('/file/<int:file_id>/download')
@login_required
def download_file(file_id):
    """Download file"""
    excel_file = ExcelFile.query.filter_by(id=file_id, user_id=current_user.id, is_active=True).first_or_404()
    
    if not excel_file.can_read():
        flash(_('You do not have permission to download this file.'), 'error')
        return redirect(url_for('main.files'))
    
    try:
        return send_file(excel_file.file_path, 
                        as_attachment=True, 
                        download_name=excel_file.original_filename)
    except Exception as e:
        current_app.logger.error(f"Download error: {str(e)}")
        flash(_('File download failed.'), 'error')
        return redirect(url_for('main.view_file', file_id=file_id))

@bp.route('/file/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file_route(file_id):
    """Delete file"""
    excel_file = ExcelFile.query.filter_by(id=file_id, user_id=current_user.id, is_active=True).first_or_404()
    
    if not excel_file.can_delete():
        flash(_('You do not have permission to delete this file.'), 'error')
        return redirect(url_for('main.files'))
    
    try:
        # Delete file from filesystem
        success, error = delete_file(excel_file.file_path)
        
        if success:
            # Mark as inactive in database
            excel_file.is_active = False
            db.session.commit()
            flash(_('File deleted successfully.'), 'success')
        else:
            flash(_(error), 'error')
            
    except Exception as e:
        current_app.logger.error(f"File deletion error: {str(e)}")
        flash(_('File deletion failed.'), 'error')
    
    return redirect(url_for('main.files'))

@bp.route('/chat')
@login_required
def chat_sessions():
    """Chat sessions overview"""
    if not current_user.can_access_system():
        flash(_('Access denied.'), 'error')
        return redirect(url_for('main.index'))
    
    sessions = current_user.chat_sessions.filter_by(is_active=True)\
                                       .order_by(ChatSession.last_activity.desc()).all()
    
    return render_template('main/chat_sessions.html',
                         title=_('Chat Sessions'),
                         sessions=sessions)

@bp.route('/chat/new', methods=['GET', 'POST'])
@login_required
def new_chat_session():
    """Create new chat session"""
    if not current_user.can_access_system():
        flash(_('Access denied.'), 'error')
        return redirect(url_for('main.index'))
    
    form = NewChatSessionForm()
    
    # Populate file choices
    files = current_user.excel_files.filter_by(is_active=True).all()
    form.excel_file_id.choices = [(f.id, f.original_filename) for f in files]
    
    if form.validate_on_submit():
        excel_file = ExcelFile.query.filter_by(id=form.excel_file_id.data, 
                                             user_id=current_user.id, 
                                             is_active=True).first()
        
        if not excel_file:
            flash(_('Selected file not found.'), 'error')
            return redirect(url_for('main.new_chat_session'))
        
        session_name = form.session_name.data or f"Chat with {excel_file.original_filename}"
        
        chat_session = ChatSession(
            user_id=current_user.id,
            excel_file_id=excel_file.id,
            session_name=session_name
        )
        
        db.session.add(chat_session)
        db.session.commit()
        
        flash(_('Chat session created successfully!'), 'success')
        return redirect(url_for('main.chat_session', session_id=chat_session.id))
    
    return render_template('main/new_chat_session.html',
                         title=_('New Chat Session'),
                         form=form,
                         files=files)

@bp.route('/chat/<int:session_id>')
@login_required
def chat_session(session_id):
    """Chat session interface"""
    session_obj = ChatSession.query.filter_by(id=session_id, 
                                             user_id=current_user.id, 
                                             is_active=True).first_or_404()
    
    if not session_obj.excel_file.can_read():
        flash(_('You do not have permission to access this chat session.'), 'error')
        return redirect(url_for('main.chat_sessions'))
    
    messages = session_obj.messages.order_by(ChatMessage.timestamp.asc()).all()
    form = ChatForm()
    form.session_id.data = session_id
    
    return render_template('main/chat_session_editable.html',
                         title=_('Chat Session'),
                         session=session_obj,
                         messages=messages,
                         form=form)

@bp.route('/chat/<int:session_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_chat_session(session_id):
    """Delete chat session"""
    session_obj = ChatSession.query.filter_by(id=session_id, 
                                             user_id=current_user.id, 
                                             is_active=True).first_or_404()
    
    # Mark as inactive instead of deleting completely
    session_obj.is_active = False
    db.session.commit()
    
    flash(_('Chat session deleted successfully.'), 'success')
    return redirect(url_for('main.chat_sessions'))

@bp.route('/api/language/<language>')
def set_language_api(language):
    """API endpoint to change language"""
    if language in current_app.config['LANGUAGES']:
        session['language'] = language
        
        # Update user preference if logged in
        if current_user.is_authenticated:
            current_user.language_preference = language
            db.session.commit()
        
        return jsonify({'status': 'success', 'language': language})
    
    return jsonify({'status': 'error', 'message': 'Invalid language'}), 400

@bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('main/privacy.html', title=_('Privacy Policy'))

@bp.route('/legal')
def legal():
    """Legal information page"""
    return render_template('main/legal.html', title=_('Legal Information'))

@bp.route('/contact')
def contact():
    """Contact information page"""
    return render_template('main/contact.html', title=_('Contact Us'))
