from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from flask_babel import gettext as _, get_locale
import os
import json
import stripe
from datetime import datetime
from werkzeug.utils import secure_filename

from app.api import bp
from app.api.chat_service import get_chat_response, transcribe_audio
from app.models import ChatSession, ChatMessage, ExcelFile, Subscription, MessageType, SubscriptionStatus
from app import db

@bp.route('/debug_log', methods=['POST'])
@login_required
def debug_log():
    """Receive debug logs from frontend"""
    data = request.get_json()
    if data and 'message' in data:
        current_app.logger.info(f"CLIENT DEBUG [{data.get('source', 'unknown')}]: {data['message']}")
    return jsonify({"status": "ok"})

@bp.route('/chat/send', methods=['POST'])
@login_required
def send_message():
    """Send a text message to chat assistant"""
    current_app.logger.info(f"Chat message received from user: {current_user.id}")
    
    if not current_user.can_access_system():
        current_app.logger.warning(f"User {current_user.id} denied access to chat")
        return jsonify({'error': _('Access denied')}), 403
    
    data = request.get_json()
    current_app.logger.debug(f"Request data: {data}")
    
    session_id = data.get('session_id')
    message_content = data.get('message', '').strip()
    
    if not session_id or not message_content:
        current_app.logger.warning(f"Invalid chat data: session_id={session_id}, message_empty={not message_content}")
        return jsonify({'error': _('Invalid request data')}), 400
    
    # Get chat session
    chat_session = ChatSession.query.filter_by(
        id=session_id,
        user_id=current_user.id,
        is_active=True
    ).first()
    
    current_app.logger.info(f"Chat session found: {chat_session is not None}")
    if chat_session:
        current_app.logger.debug(f"Session: {chat_session.id}, Excel file: {chat_session.excel_file.filename if chat_session.excel_file else 'None'}")
    
    if not chat_session:
        return jsonify({'error': _('Chat session not found')}), 404
    
    if not chat_session.excel_file.can_read():
        return jsonify({'error': _('No permission to access this file')}), 403
    
    try:
        # Save user message
        user_message = ChatMessage(
            session_id=session_id,
            message_type=MessageType.TEXT,
            content=message_content,
            language=str(get_locale()),
            is_user_message=True
        )
        db.session.add(user_message)
        
        # Get previous messages for context
        previous_messages = chat_session.messages.order_by(ChatMessage.timestamp.asc()).all()
        
        # Get assistant response
        assistant_response, error = get_chat_response(
            previous_messages,
            chat_session.excel_file,
            str(get_locale()),
            message_content
        )
        
        if error:
            return jsonify({'error': error}), 500
        
        # Save assistant response
        assistant_message = ChatMessage(
            session_id=session_id,
            message_type=MessageType.TEXT,
            content=assistant_response,
            language=str(get_locale()),
            is_user_message=False
        )
        db.session.add(assistant_message)
        
        # Update session activity
        chat_session.last_activity = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'timestamp': user_message.timestamp.isoformat(),
                'is_user': True
            },
            'assistant_message': {
                'id': assistant_message.id,
                'content': assistant_message.content,
                'timestamp': assistant_message.timestamp.isoformat(),
                'is_user': False
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Chat send error: {str(e)}")
        return jsonify({'error': _('Error processing message')}), 500

@bp.route('/chat/voice', methods=['POST'])
@login_required
def send_voice_message():
    """Send a voice message to chat assistant"""
    if not current_user.can_access_system():
        return jsonify({'error': _('Access denied')}), 403
    
    session_id = request.form.get('session_id')
    audio_file = request.files.get('audio')
    
    if not session_id or not audio_file:
        return jsonify({'error': _('Invalid request data')}), 400
    
    # Get chat session
    chat_session = ChatSession.query.filter_by(
        id=session_id,
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not chat_session:
        return jsonify({'error': _('Chat session not found')}), 404
    
    if not chat_session.excel_file.can_read():
        return jsonify({'error': _('No permission to access this file')}), 403
    
    try:
        # Save audio file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"voice_{session_id}_{timestamp}_{secure_filename(audio_file.filename)}"
        
        # Create audio directory if it doesn't exist
        audio_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f"user_{current_user.id}", "audio")
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)
        
        audio_path = os.path.join(audio_dir, filename)
        audio_file.save(audio_path)
        
        # Transcribe audio
        language_code = str(get_locale())
        whisper_language = 'de' if language_code == 'de' else 'ru' if language_code == 'ru' else 'en'
        
        transcription, error = transcribe_audio(audio_path, whisper_language)
        
        if error:
            return jsonify({'error': error}), 500
        
        if not transcription.strip():
            return jsonify({'error': _('No speech detected in audio')}), 400
        
        # Save user voice message
        user_message = ChatMessage(
            session_id=session_id,
            message_type=MessageType.VOICE,
            content=transcription,
            language=language_code,
            is_user_message=True,
            audio_file_path=audio_path,
            transcription=transcription
        )
        db.session.add(user_message)
        
        # Get previous messages for context
        previous_messages = chat_session.messages.order_by(ChatMessage.timestamp.asc()).all()
        
        # Get assistant response
        assistant_response, error = get_chat_response(
            previous_messages,
            chat_session.excel_file,
            language_code,
            transcription
        )
        
        if error:
            return jsonify({'error': error}), 500
        
        # Save assistant response
        assistant_message = ChatMessage(
            session_id=session_id,
            message_type=MessageType.TEXT,
            content=assistant_response,
            language=language_code,
            is_user_message=False
        )
        db.session.add(assistant_message)
        
        # Update session activity
        chat_session.last_activity = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'transcription': transcription,
                'timestamp': user_message.timestamp.isoformat(),
                'is_user': True,
                'type': 'voice'
            },
            'assistant_message': {
                'id': assistant_message.id,
                'content': assistant_message.content,
                'timestamp': assistant_message.timestamp.isoformat(),
                'is_user': False,
                'type': 'text'
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Voice chat error: {str(e)}")
        return jsonify({'error': _('Error processing voice message')}), 500

@bp.route('/chat/sessions/<int:session_id>/messages')
@login_required
def get_messages(session_id):
    """Get messages for a chat session"""
    if not current_user.can_access_system():
        return jsonify({'error': _('Access denied')}), 403
    
    chat_session = ChatSession.query.filter_by(
        id=session_id,
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not chat_session:
        return jsonify({'error': _('Chat session not found')}), 404
    
    messages = chat_session.messages.order_by(ChatMessage.timestamp.asc()).all()
    
    messages_data = []
    for msg in messages:
        message_data = {
            'id': msg.id,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'is_user': msg.is_user_message,
            'type': msg.message_type.value,
            'language': msg.language
        }
        
        if msg.message_type == MessageType.VOICE and msg.transcription:
            message_data['transcription'] = msg.transcription
        
        messages_data.append(message_data)
    
    return jsonify({'messages': messages_data})

@bp.route('/files/<int:file_id>/data')
@login_required
def get_file_data(file_id):
    """Get Excel file data for display"""
    if not current_user.can_access_system():
        return jsonify({'error': _('Access denied')}), 403
    
    excel_file = ExcelFile.query.filter_by(
        id=file_id,
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not excel_file:
        return jsonify({'error': _('File not found')}), 404
    
    if not excel_file.can_read():
        return jsonify({'error': _('No permission to access this file')}), 403
    
    try:
        sheet_name = request.args.get('sheet')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        from app.main.utils import load_excel_data
        data, error = load_excel_data(excel_file.file_path, sheet_name, offset + per_page)
        
        if error:
            return jsonify({'error': error}), 500
        
        # Paginate data
        paginated_data = data['data'][offset:offset + per_page]
        
        return jsonify({
            'data': paginated_data,
            'columns': data['columns'],
            'total_rows': data['total_rows'],
            'page': page,
            'per_page': per_page,
            'has_more': offset + per_page < data['total_rows']
        })
        
    except Exception as e:
        current_app.logger.error(f"File data API error: {str(e)}")
        return jsonify({'error': _('Error loading file data')}), 500

@bp.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        endpoint_secret = current_app.config['STRIPE_WEBHOOK_SECRET']
        
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        
        # Handle the event
        if event['type'] == 'invoice.payment_succeeded':
            # Payment succeeded, activate subscription
            subscription_id = event['data']['object']['subscription']
            
            subscription_record = Subscription.query.filter_by(
                stripe_subscription_id=subscription_id
            ).first()
            
            if subscription_record:
                subscription_record.status = SubscriptionStatus.ACTIVE
                
                # Update period dates
                stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                subscription_record.current_period_start = datetime.fromtimestamp(
                    stripe_subscription.current_period_start
                )
                subscription_record.current_period_end = datetime.fromtimestamp(
                    stripe_subscription.current_period_end
                )
                
                db.session.commit()
        
        elif event['type'] == 'invoice.payment_failed':
            # Payment failed, mark subscription as past due
            subscription_id = event['data']['object']['subscription']
            
            subscription_record = Subscription.query.filter_by(
                stripe_subscription_id=subscription_id
            ).first()
            
            if subscription_record:
                subscription_record.status = SubscriptionStatus.PAST_DUE
                db.session.commit()
        
        elif event['type'] == 'customer.subscription.deleted':
            # Subscription cancelled
            subscription_id = event['data']['object']['id']
            
            subscription_record = Subscription.query.filter_by(
                stripe_subscription_id=subscription_id
            ).first()
            
            if subscription_record:
                subscription_record.status = SubscriptionStatus.CANCELLED
                db.session.commit()
        
        return jsonify({'status': 'success'})
        
    except ValueError as e:
        current_app.logger.error(f"Invalid Stripe payload: {str(e)}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        current_app.logger.error(f"Invalid Stripe signature: {str(e)}")
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        current_app.logger.error(f"Stripe webhook error: {str(e)}")
        return jsonify({'error': 'Webhook error'}), 500
