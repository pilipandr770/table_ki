from flask import request, jsonify, current_app
import os
import uuid
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from flask_babel import gettext as _
from datetime import datetime

from app.api import bp
from app.api.chat_service import transcribe_audio, get_chat_response
from app.models import ChatSession, ChatMessage, MessageType
from app import db

ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'webm'}

def allowed_audio_file(filename):
    """Check if the file is an allowed audio file"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

@bp.route('/send_voice_message', methods=['POST'])
@login_required
def process_voice_message():
    """Process voice message from user"""
    current_app.logger.info(f"Voice message received from user: {current_user.id}")
    
    # Verbose debugging of request
    current_app.logger.info(f"Request method: {request.method}")
    current_app.logger.info(f"Request content type: {request.content_type}")
    current_app.logger.info(f"Form data: {request.form}")
    current_app.logger.info(f"Files: {list(request.files.keys()) if request.files else 'No files'}")
    
    if 'audio' in request.files:
        audio_file = request.files['audio']
        current_app.logger.info(f"Audio file name: {audio_file.filename}")
        current_app.logger.info(f"Audio file content type: {audio_file.content_type}")
        current_app.logger.info(f"Audio file size: {audio_file.content_length if hasattr(audio_file, 'content_length') else 'unknown'}")
    else:
        current_app.logger.warning("No audio file in request")
    
    if not current_user.can_access_system():
        current_app.logger.warning(f"User {current_user.id} denied access to voice chat")
        return jsonify({'error': _('Access denied')}), 403
    
    # Get form data
    session_id = request.form.get('session_id')
    language = request.form.get('language', 'en')
    
    current_app.logger.info(f"Voice processing: session_id={session_id}, language={language}")
    
    # Check if session exists and belongs to current user
    try:
        chat_session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
        if not chat_session:
            current_app.logger.warning(f"Voice chat session not found: {session_id}")
            return jsonify({'error': _('Chat session not found')}), 404
        
        current_app.logger.info(f"Voice chat session found: {chat_session.id}, Excel file: {chat_session.excel_file.filename if chat_session.excel_file else 'None'}")
    except Exception as e:
        current_app.logger.error(f"Error finding chat session: {str(e)}")
        return jsonify({'error': _('Error accessing chat session')}), 500
    
    # Check if there's a file in the request
    if 'audio' not in request.files:
        current_app.logger.warning("No audio file in request files")
        return jsonify({'error': _('No audio file provided')}), 400
    
    audio_file = request.files['audio']
    current_app.logger.info(f"Processing audio file: {audio_file.filename}")
    
    if audio_file.filename == '':
        current_app.logger.warning("Empty audio filename")
        return jsonify({'error': _('Empty audio file')}), 400
    
    if not allowed_audio_file(audio_file.filename):
        current_app.logger.warning(f"Invalid audio format: {audio_file.filename}")
        return jsonify({'error': _('Invalid audio format. Allowed formats: mp3, wav, ogg, webm')}), 400
    
    try:
        # Save audio file temporarily
        filename = secure_filename(f"{uuid.uuid4()}.{audio_file.filename.rsplit('.', 1)[1].lower()}")
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'voice_messages')
        
        # Create directory if it doesn't exist
        os.makedirs(upload_folder, exist_ok=True)
        
        audio_path = os.path.join(upload_folder, filename)
        current_app.logger.info(f"Saving audio to: {audio_path}")
        audio_file.save(audio_path)
        
        # Check if file was saved
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            current_app.logger.info(f"Audio file saved successfully. Size: {file_size} bytes")
        else:
            current_app.logger.warning("Failed to save audio file")
            return jsonify({'error': _('Failed to save audio file')}), 500
        
        # Transcribe audio
        current_app.logger.info(f"Transcribing audio with language: {language}")
        transcript, error = transcribe_audio(audio_path, language)
        current_app.logger.info(f"Transcription result: {transcript}")
        current_app.logger.info(f"Transcription error: {error}")
        
        # Delete temporary file
        try:
            os.remove(audio_path)
            current_app.logger.info(f"Temporary audio file deleted: {audio_path}")
        except Exception as e:
            current_app.logger.warning(f"Failed to delete temporary audio file: {audio_path}, Error: {str(e)}")
        
        if error:
            current_app.logger.error(f"Transcription error: {error}")
            return jsonify({'error': error}), 500
        
        if not transcript:
            current_app.logger.warning("Empty transcription result")
            return jsonify({'error': _('Failed to transcribe audio')}), 500
            
        current_app.logger.info(f"Transcription successful: '{transcript}'")
        
        # Save transcription as user message
        try:
            user_message = ChatMessage(
                chat_session_id=chat_session.id,
                is_user_message=True,
                content=transcript,
                message_type=MessageType.VOICE,
                timestamp=datetime.utcnow()
            )
            db.session.add(user_message)
            current_app.logger.info("User voice message saved to database")
            
            # Update chat session
            chat_session.last_activity = datetime.utcnow()
            db.session.commit()
            current_app.logger.info("Chat session updated")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving user message: {str(e)}")
            return jsonify({'error': _('Database error')}), 500
        
        # Get AI response
        try:
            excel_file = chat_session.excel_file
            messages = chat_session.messages.order_by(ChatMessage.timestamp.asc()).all()
            
            current_app.logger.info(f"Getting AI response with {len(messages)} previous messages")
            assistant_response, error = get_chat_response(
                excel_file=excel_file,
                messages=messages,
                language=language,
                bypass_openai=current_app.config.get('BYPASS_OPENAI', False)
            )
            current_app.logger.info(f"AI response received: {assistant_response[:50]}...")
        except Exception as e:
            current_app.logger.error(f"Error getting AI response: {str(e)}")
            return jsonify({
                'success': True,
                'transcript': transcript,
                'error': _('Error getting AI response')
            })
        
        if error:
            current_app.logger.warning(f"AI response error: {error}")
            return jsonify({
                'success': True,
                'transcript': transcript,
                'error': error
            })
        
        # Save assistant response
        try:
            assistant_message = ChatMessage(
                chat_session_id=chat_session.id,
                is_user_message=False,
                content=assistant_response,
                message_type=MessageType.TEXT,
                timestamp=datetime.utcnow()
            )
            db.session.add(assistant_message)
            
            # Update chat session
            chat_session.last_activity = datetime.utcnow()
            db.session.commit()
            current_app.logger.info("Assistant response saved to database")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving assistant message: {str(e)}")
            return jsonify({
                'success': True,
                'transcript': transcript,
                'error': _('Error saving assistant response')
            })
        
        current_app.logger.info("Voice processing completed successfully")
        return jsonify({
            'success': True,
            'transcript': transcript,
            'response': assistant_response
        })
        
    except Exception as e:
        current_app.logger.error(f"Error processing voice message: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500
