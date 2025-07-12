from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
import re

from app.models import ExcelFile, ChatSession, ChatMessage, MessageType
from app.main.excel_service import modify_excel_data, add_excel_row, delete_excel_row, can_perform_action
from app import db

bp = Blueprint('ai_actions', __name__, url_prefix='/ai-actions')

@bp.route('/process-message', methods=['POST'])
@login_required
def process_message():
    """
    Обрабатывает запрос от чат-модели на выполнение действий с таблицами
    
    JSON параметры:
    - message_id: ID сообщения ассистента
    - action_type: тип действия ('update_cell', 'add_row', 'delete_row')
    - parameters: параметры действия (зависят от типа действия)
    """
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'Отсутствуют данные в запросе'
        }), 400
    
    message_id = data.get('message_id')
    action_type = data.get('action_type')
    parameters = data.get('parameters', {})
    
    # Проверяем наличие необходимых параметров
    if not message_id or not action_type:
        return jsonify({
            'success': False,
            'error': 'Отсутствуют необходимые параметры: message_id, action_type'
        }), 400
    
    # Получаем сообщение и связанные объекты
    message = ChatMessage.query.filter_by(id=message_id).first()
    if not message:
        return jsonify({
            'success': False,
            'error': 'Сообщение не найдено'
        }), 404
    
    # Проверяем, что сообщение принадлежит текущему пользователю
    if message.chat_session.user_id != current_user.id:
        return jsonify({
            'success': False,
            'error': 'У вас нет доступа к этому сообщению'
        }), 403
    
    # Получаем связанный файл Excel
    chat_session = message.chat_session
    excel_file = chat_session.excel_file
    
    if not excel_file:
        return jsonify({
            'success': False,
            'error': 'Для этого чата не прикреплен файл Excel'
        }), 400
    
    # Выполняем действие в зависимости от типа
    result = None
    error = None
    
    if action_type == 'update_cell':
        if not can_perform_action(excel_file, 'write'):
            return jsonify({
                'success': False,
                'error': 'У вас нет прав на изменение данных в этом файле'
            }), 403
        
        row_index = parameters.get('row_index')
        column = parameters.get('column')
        value = parameters.get('value')
        sheet_name = parameters.get('sheet')
        
        if row_index is None or not column or value is None:
            return jsonify({
                'success': False,
                'error': 'Для обновления ячейки необходимы параметры: row_index, column, value'
            }), 400
        
        result, error = modify_excel_data(excel_file.file_path, sheet_name, int(row_index), column, value)
        
    elif action_type == 'add_row':
        if not can_perform_action(excel_file, 'write'):
            return jsonify({
                'success': False,
                'error': 'У вас нет прав на изменение данных в этом файле'
            }), 403
        
        row_data = parameters.get('row_data')
        sheet_name = parameters.get('sheet')
        
        if not row_data:
            return jsonify({
                'success': False,
                'error': 'Для добавления строки необходим параметр row_data'
            }), 400
        
        result, error = add_excel_row(excel_file.file_path, sheet_name, row_data)
        
    elif action_type == 'delete_row':
        if not can_perform_action(excel_file, 'delete'):
            return jsonify({
                'success': False,
                'error': 'У вас нет прав на удаление данных в этом файле'
            }), 403
        
        row_index = parameters.get('row_index')
        sheet_name = parameters.get('sheet')
        
        if row_index is None:
            return jsonify({
                'success': False,
                'error': 'Для удаления строки необходим параметр row_index'
            }), 400
        
        result, error = delete_excel_row(excel_file.file_path, sheet_name, int(row_index))
        
    else:
        return jsonify({
            'success': False,
            'error': f'Неизвестный тип действия: {action_type}'
        }), 400
    
    # Возвращаем результат
    if result:
        # Добавляем системное сообщение об успешном выполнении действия
        system_message = ChatMessage(
            chat_session_id=chat_session.id,
            type=MessageType.SYSTEM,
            is_user_message=False,
            content=f'Действие "{action_type}" выполнено успешно!'
        )
        db.session.add(system_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Действие выполнено успешно',
            'system_message_id': system_message.id
        })
    else:
        return jsonify({
            'success': False,
            'error': error or 'Произошла ошибка при выполнении действия'
        }), 400


@bp.route('/parse-ai-message', methods=['POST'])
@login_required
def parse_ai_message():
    """
    Анализирует текстовый ответ AI на наличие команд изменения данных и выполняет их
    
    JSON параметры:
    - message_id: ID сообщения ассистента
    """
    data = request.json
    
    if not data or 'message_id' not in data:
        return jsonify({
            'success': False,
            'error': 'Отсутствует ID сообщения'
        }), 400
    
    message_id = data['message_id']
    message = ChatMessage.query.filter_by(id=message_id).first()
    
    if not message:
        return jsonify({
            'success': False,
            'error': 'Сообщение не найдено'
        }), 404
    
    # Проверяем, что сообщение принадлежит текущему пользователю
    if message.chat_session.user_id != current_user.id:
        return jsonify({
            'success': False,
            'error': 'У вас нет доступа к этому сообщению'
        }), 403
    
    # Получаем связанный файл Excel
    chat_session = message.chat_session
    excel_file = chat_session.excel_file
    
    if not excel_file:
        return jsonify({
            'success': False,
            'error': 'Для этого чата не прикреплен файл Excel'
        }), 400
    
    # Анализируем текст сообщения и ищем команды на изменение данных
    content = message.content
    actions_performed = []
    errors = []
    
    # Проверяем права доступа
    can_write = can_perform_action(excel_file, 'write')
    can_delete = can_perform_action(excel_file, 'delete')
    
    # Паттерны для поиска команд
    update_pattern = r"update\s+(?:the\s+)?(?:value\s+in\s+)?row\s+(\d+)(?:,\s*|\s+)(?:column\s+)?['\"]?([^'\"]+)['\"]?\s+to\s+['\"]?([^'\"]+)['\"]?"
    add_row_pattern = r"add\s+(?:a\s+)?new\s+row\s+with\s+(.+)"
    delete_row_pattern = r"delete\s+row\s+(\d+)"
    
    # 1. Обрабатываем команды на обновление ячеек
    if can_write:
        update_matches = re.finditer(update_pattern, content, re.IGNORECASE)
        for match in update_matches:
            row_index = int(match.group(1)) - 1  # Преобразуем из 1-индексации в 0-индексацию
            column = match.group(2).strip()
            value = match.group(3).strip()
            
            # Выполняем обновление
            sheet_name = None  # В будущем можно добавить извлечение имени листа из текста
            result, error = modify_excel_data(excel_file.file_path, sheet_name, row_index, column, value)
            
            if result:
                actions_performed.append(f"Updated row {row_index+1}, column '{column}' to '{value}'")
            else:
                errors.append(f"Failed to update cell: {error}")
    
    # 2. Обрабатываем команды на добавление строк
    if can_write:
        add_matches = re.finditer(add_row_pattern, content, re.IGNORECASE)
        for match in add_matches:
            row_data_str = match.group(1).strip()
            
            # Парсим данные строки (формат: key1='value1', key2='value2')
            row_data = {}
            kv_pattern = r"([^=,]+)=(?:'|\")([^'\"]+)(?:'|\")"
            kv_matches = re.finditer(kv_pattern, row_data_str)
            
            for kv_match in kv_matches:
                key = kv_match.group(1).strip()
                value = kv_match.group(2).strip()
                row_data[key] = value
            
            if row_data:
                sheet_name = None
                result, error = add_excel_row(excel_file.file_path, sheet_name, row_data)
                
                if result:
                    actions_performed.append(f"Added new row with data: {row_data}")
                else:
                    errors.append(f"Failed to add row: {error}")
    
    # 3. Обрабатываем команды на удаление строк
    if can_delete:
        delete_matches = re.finditer(delete_row_pattern, content, re.IGNORECASE)
        for match in delete_matches:
            row_index = int(match.group(1)) - 1  # Преобразуем из 1-индексации в 0-индексацию
            
            sheet_name = None
            result, error = delete_excel_row(excel_file.file_path, sheet_name, row_index)
            
            if result:
                actions_performed.append(f"Deleted row {row_index+1}")
            else:
                errors.append(f"Failed to delete row: {error}")
    
    # Создаем системное сообщение с отчетом о выполненных действиях
    if actions_performed:
        actions_text = "\n".join(actions_performed)
        errors_text = "\n".join(errors) if errors else ""
        
        system_message_content = f"Выполненные действия с таблицей:\n{actions_text}"
        if errors_text:
            system_message_content += f"\n\nОшибки:\n{errors_text}"
        
        system_message = ChatMessage(
            chat_session_id=chat_session.id,
            type=MessageType.SYSTEM,
            is_user_message=False,
            content=system_message_content
        )
        db.session.add(system_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'actions_performed': actions_performed,
            'errors': errors,
            'system_message_id': system_message.id
        })
    
    return jsonify({
        'success': True,
        'message': 'В сообщении не найдены команды для изменения данных'
    })
