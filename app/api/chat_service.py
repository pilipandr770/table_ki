import openai
import os
import json
from flask import current_app
from flask_babel import gettext as _
from app.main.utils import get_excel_summary, load_excel_data

def get_system_prompt(language='en', excel_file=None):
    """Get system prompt for chat assistant in specified language"""
    
    # Определим уровень доступа к таблице
    permission_info = {
        'en': "read-only access (you can only view the data)",
        'de': "nur Lesezugriff (Sie können die Daten nur anzeigen)",
        'ru': "доступ только для чтения (вы можете только просматривать данные)"
    }
    
    if excel_file:
        if excel_file.permission_mode.value == 'read_write':
            permission_info = {
                'en': "read and write access (you can view and modify the data)",
                'de': "Lese- und Schreibzugriff (Sie können die Daten anzeigen und ändern)",
                'ru': "доступ на чтение и запись (вы можете просматривать и изменять данные)"
            }
        elif excel_file.permission_mode.value == 'read_write_delete':
            permission_info = {
                'en': "full access (you can view, modify, and delete the data)",
                'de': "voller Zugriff (Sie können die Daten anzeigen, ändern und löschen)",
                'ru': "полный доступ (вы можете просматривать, изменять и удалять данные)"
            }
    
    prompts = {
        'en': f"""You are an expert Excel data analyst assistant. You help users analyze, understand, and work with their Excel files. 

You have {permission_info['en']} to the Excel file and can:
- Analyze data patterns and trends
- Answer questions about the data
- Suggest data insights
- Help with data interpretation
- Provide summaries and statistics

For this file, you have the following capabilities:
{"- Modify cell values (you can update existing data)" if excel_file and excel_file.can_write() else ""}
{"- Add new rows to the table" if excel_file and excel_file.can_write() else ""}
{"- Delete rows from the table" if excel_file and excel_file.can_delete() else ""}

To modify data, tell the user you'll help them modify the data and provide specific instructions like:
1. To update a cell: "I'll update the value in row 5, column 'Price' to 25.99"
2. To add a new row: "I'll add a new row with Name='Product X', Price=19.99, Category='Electronics'"
3. To delete a row: "I'll delete row 8 which contains the outdated entry"

Always be helpful, accurate, and provide clear explanations. If you cannot perform a specific action due to permission limitations, explain this clearly to the user.

When analyzing data, focus on practical insights and actionable information.""",
        
        'de': f"""Sie sind ein Experte für Excel-Datenanalyse. Sie helfen Benutzern beim Analysieren, Verstehen und Arbeiten mit ihren Excel-Dateien.

Sie haben {permission_info['de']} zu der Excel-Datei und können:
- Datenmuster und Trends analysieren
- Fragen zu den Daten beantworten
- Dateneinblicke vorschlagen
- Bei der Dateninterpretation helfen
- Zusammenfassungen und Statistiken bereitstellen

Für diese Datei haben Sie folgende Möglichkeiten:
{"- Zellinhalte ändern (Sie können vorhandene Daten aktualisieren)" if excel_file and excel_file.can_write() else ""}
{"- Neue Zeilen zur Tabelle hinzufügen" if excel_file and excel_file.can_write() else ""}
{"- Zeilen aus der Tabelle löschen" if excel_file and excel_file.can_delete() else ""}

Seien Sie immer hilfsbereit, genau und geben Sie klare Erklärungen. Wenn Sie aufgrund von Berechtigungseinschränkungen eine bestimmte Aktion nicht ausführen können, erklären Sie dies dem Benutzer klar.

Konzentrieren Sie sich bei der Datenanalyse auf praktische Einblicke und umsetzbare Informationen.""",
        
        'ru': f"""Вы эксперт-аналитик данных Excel. Вы помогаете пользователям анализировать, понимать и работать с их Excel-файлами.

У вас есть {permission_info['ru']} к данной Excel-таблице, и вы можете:
- Анализировать паттерны и тренды данных
- Отвечать на вопросы о данных
- Предлагать инсайты данных
- Помогать с интерпретацией данных
- Предоставлять сводки и статистику

Для этого файла у вас есть следующие возможности:
{"- Изменять значения в ячейках (вы можете обновлять существующие данные)" if excel_file and excel_file.can_write() else ""}
{"- Добавлять новые строки в таблицу" if excel_file and excel_file.can_write() else ""}
{"- Удалять строки из таблицы" if excel_file and excel_file.can_delete() else ""}

Чтобы изменить данные, скажите пользователю, что вы поможете ему изменить данные, и дайте конкретные инструкции, например:
1. Для обновления ячейки: "Я обновлю значение в строке 5, столбце 'Цена' на 25.99"
2. Для добавления новой строки: "Я добавлю новую строку с Наименование='Продукт X', Цена=19.99, Категория='Электроника'"
3. Для удаления строки: "Я удалю строку 8, которая содержит устаревшую запись"

Всегда будьте полезными, точными и давайте четкие объяснения. Если вы не можете выполнить определенное действие из-за ограничений разрешений, четко объясните это пользователю.

При анализе данных сосредоточьтесь на практических инсайтах и применимой информации."""
    }
    
    return prompts.get(language, prompts['en'])

def format_excel_data_for_prompt(excel_file, sheet_name=None, max_rows=100):
    """Format Excel data for inclusion in chat prompt"""
    try:
        # Get file summary
        summary, error = get_excel_summary(excel_file.file_path)
        if error:
            return f"Error loading file data: {error}"
        
        # Get specific sheet data if requested
        if sheet_name:
            data, error = load_excel_data(excel_file.file_path, sheet_name, max_rows)
            if error:
                return f"Error loading sheet data: {error}"
            
            formatted_data = f"""
File: {excel_file.original_filename}
Sheet: {sheet_name}
Columns: {', '.join(data['columns'])}
Total Rows: {data['total_rows']}
Data Types: {json.dumps(data['dtypes'], indent=2)}

Sample Data (first {min(len(data['data']), max_rows)} rows):
{json.dumps(data['data'][:max_rows], indent=2)}
"""
        else:
            # Provide general file summary
            formatted_data = f"""
File: {excel_file.original_filename}
Sheets: {', '.join(summary['file_info']['sheet_names'])}
Total Sheets: {summary['file_info']['sheet_count']}

Sheet Summaries:
"""
            for sheet_name, sheet_info in summary['sheets'].items():
                formatted_data += f"""
- {sheet_name}: {sheet_info['row_count']} rows, {sheet_info['column_count']} columns
  Columns: {', '.join(sheet_info['columns'])}
"""
        
        return formatted_data.strip()
        
    except Exception as e:
        current_app.logger.error(f"Error formatting Excel data: {str(e)}")
        return f"Error formatting file data: {str(e)}"

def get_chat_response(messages, excel_file, language='en', user_question=None):
    """Get response from OpenAI chat completion"""
    try:
        current_app.logger.info(f"Chat request received: language={language}, user_question={user_question}")
        current_app.logger.debug(f"Excel file: {excel_file.filename if excel_file else 'None'}")
        current_app.logger.debug(f"Message count: {len(messages) if messages else 0}")
        
        # Check if we're in bypass mode
        bypass_mode = current_app.config.get('BYPASS_OPENAI', False)
        current_app.logger.info(f"Bypass mode: {bypass_mode}")
        
        if bypass_mode:
            current_app.logger.info("Using mock response for development mode")
            mock_responses = {
                'en': f"This is a mock response for development mode. Your question was: '{user_question}'. In a real implementation, this would analyze your Excel file '{excel_file.original_filename if excel_file else 'unknown'}' and provide insights.",
                'de': f"Dies ist eine Mock-Antwort für den Entwicklungsmodus. Ihre Frage war: '{user_question}'. In einer echten Implementierung würde Ihre Excel-Datei '{excel_file.original_filename if excel_file else 'unbekannt'}' analysiert und Einblicke bereitgestellt.",
                'ru': f"Это тестовый ответ для режима разработки. Ваш вопрос был: '{user_question}'. В реальной реализации это проанализировало бы ваш Excel-файл '{excel_file.original_filename if excel_file else 'неизвестно'}' и предоставило бы понимание."
            }
            response = mock_responses.get(language, mock_responses['en'])
            current_app.logger.info(f"Mock response generated: {response[:50]}...")
            return response, None
        
        openai.api_key = current_app.config['OPENAI_API_KEY']
        
        if not openai.api_key:
            return None, _("OpenAI API key not configured")
        
        # Build conversation messages
        conversation_messages = [
            {"role": "system", "content": get_system_prompt(language, excel_file)}
        ]
        
        # Add Excel file context
        excel_context = format_excel_data_for_prompt(excel_file)
        conversation_messages.append({
            "role": "system", 
            "content": f"Here is the Excel file data you're working with:\n\n{excel_context}"
        })
        
        # Add conversation history
        for msg in messages:
            role = "user" if msg.is_user_message else "assistant"
            conversation_messages.append({
                "role": role,
                "content": msg.content
            })
        
        # Add current user question if provided
        if user_question:
            conversation_messages.append({
                "role": "user",
                "content": user_question
            })
        
        # Get response from OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_messages,
            max_tokens=1000,
            temperature=0.7,
            stream=False
        )
        
        assistant_response = response.choices[0].message.content.strip()
        return assistant_response, None
        
    except openai.error.AuthenticationError:
        return None, _("OpenAI API authentication failed")
    except openai.error.RateLimitError:
        return None, _("OpenAI API rate limit exceeded. Please try again later.")
    except openai.error.APIError as e:
        current_app.logger.error(f"OpenAI API error: {str(e)}")
        return None, _("OpenAI API error. Please try again later.")
    except Exception as e:
        current_app.logger.error(f"Chat response error: {str(e)}")
        return None, _("Error generating response. Please try again.")

def transcribe_audio(audio_file_path, language='en'):
    """Transcribe audio using OpenAI Whisper"""
    current_app.logger.info(f"[TRANSCRIBE] Starting audio transcription for file: {audio_file_path}")
    current_app.logger.info(f"[TRANSCRIBE] Language: {language}")
    
    # Check if the file exists and is readable
    if not os.path.exists(audio_file_path):
        current_app.logger.error(f"[TRANSCRIBE] Audio file does not exist: {audio_file_path}")
        return None, _("Audio file not found")
        
    try:
        file_size = os.path.getsize(audio_file_path)
        current_app.logger.info(f"[TRANSCRIBE] Audio file size: {file_size} bytes")
    except Exception as e:
        current_app.logger.warning(f"[TRANSCRIBE] Error getting file size: {str(e)}")
    
    # Test if we can open and read the file
    try:
        with open(audio_file_path, 'rb') as test_file:
            sample = test_file.read(1024)
            current_app.logger.info(f"[TRANSCRIBE] Successfully read {len(sample)} bytes from file")
    except Exception as e:
        current_app.logger.error(f"[TRANSCRIBE] Cannot read audio file: {str(e)}")
        return None, _("Cannot read audio file")
    
    try:
        # Always use mock transcriptions for testing
        current_app.logger.info("[TRANSCRIBE] Using mock transcription for development mode")
        mock_transcripts = {
            'en': "This is a mock transcription for development mode. Your audio was processed successfully.",
            'de': "Dies ist eine Mock-Transkription für den Entwicklungsmodus. Ihr Audio wurde erfolgreich verarbeitet.",
            'ru': "Это тестовая транскрипция для режима разработки. Ваш аудио был успешно обработан."
        }
        transcript_text = mock_transcripts.get(language, mock_transcripts['en'])
        current_app.logger.info(f"[TRANSCRIBE] Mock transcription: {transcript_text}")
        return transcript_text, None
        
        # The following code will only run if we remove the return statement above
        current_app.logger.info("[TRANSCRIBE] Getting OpenAI API key")
        openai.api_key = current_app.config['OPENAI_API_KEY']
        
        if not openai.api_key:
            current_app.logger.error("[TRANSCRIBE] OpenAI API key not configured")
            return None, _("OpenAI API key not configured")
        
        current_app.logger.info("[TRANSCRIBE] Opening audio file for transcription")
        with open(audio_file_path, 'rb') as audio_file:
            current_app.logger.info("[TRANSCRIBE] Calling OpenAI Whisper API")
            transcript = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                language=language if language != 'en' else None
            )
            current_app.logger.info("[TRANSCRIBE] OpenAI API call successful")
        
        transcript_text = transcript.text.strip()
        current_app.logger.info(f"[TRANSCRIBE] Transcription result: {transcript_text[:100]}...")
        return transcript_text, None
        
    except openai.error.AuthenticationError as e:
        current_app.logger.error(f"[TRANSCRIBE] OpenAI authentication error: {str(e)}")
        return None, _("OpenAI API authentication failed")
    except openai.error.RateLimitError as e:
        current_app.logger.error(f"[TRANSCRIBE] OpenAI rate limit error: {str(e)}")
        return None, _("OpenAI API rate limit exceeded. Please try again later.")
    except Exception as e:
        current_app.logger.error(f"[TRANSCRIBE] Audio transcription error: {str(e)}")
        import traceback
        current_app.logger.error(f"[TRANSCRIBE] Traceback: {traceback.format_exc()}")
        return None, _("Error transcribing audio. Please try again.")
