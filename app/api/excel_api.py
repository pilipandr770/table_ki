from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user

from app.models import ExcelFile
from app.main.excel_service import modify_excel_data, add_excel_row, delete_excel_row, can_perform_action

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/excel/<int:file_id>/data', methods=['GET'])
@login_required
def get_excel_data(file_id):
    """
    API для получения данных из Excel файла
    
    GET параметры:
    - sheet: имя листа (опционально)
    """
    excel_file = ExcelFile.query.filter_by(id=file_id, user_id=current_user.id, is_active=True).first_or_404()
    
    # Проверяем права доступа
    if not can_perform_action(excel_file, 'read'):
        return jsonify({
            'success': False,
            'error': 'У вас нет прав на чтение данного файла'
        }), 403
    
    sheet_name = request.args.get('sheet')
    
    from app.main.utils import load_excel_data
    data, error = load_excel_data(excel_file.file_path, sheet_name)
    
    if error:
        return jsonify({
            'success': False,
            'error': error
        }), 400
        
    return jsonify({
        'success': True,
        'data': data
    })

@bp.route('/excel/<int:file_id>/cell', methods=['PUT'])
@login_required
def update_excel_cell(file_id):
    """
    API для обновления значения ячейки
    
    JSON параметры:
    - sheet: имя листа (опционально)
    - row: индекс строки (начиная с 0)
    - column: имя колонки
    - value: новое значение
    """
    excel_file = ExcelFile.query.filter_by(id=file_id, user_id=current_user.id, is_active=True).first_or_404()
    
    # Проверяем права доступа
    if not can_perform_action(excel_file, 'write'):
        return jsonify({
            'success': False,
            'error': 'У вас нет прав на изменение данного файла'
        }), 403
    
    data = request.json
    
    if not data or 'row' not in data or 'column' not in data or 'value' not in data:
        return jsonify({
            'success': False,
            'error': 'Отсутствуют необходимые параметры: row, column, value'
        }), 400
        
    sheet_name = data.get('sheet')
    row_index = int(data['row'])
    column = data['column']
    value = data['value']
    
    success, error = modify_excel_data(excel_file.file_path, sheet_name, row_index, column, value)
    
    if not success:
        return jsonify({
            'success': False,
            'error': error
        }), 400
        
    return jsonify({
        'success': True,
        'message': 'Ячейка успешно обновлена'
    })

@bp.route('/excel/<int:file_id>/row', methods=['POST'])
@login_required
def add_row(file_id):
    """
    API для добавления новой строки
    
    JSON параметры:
    - sheet: имя листа (опционально)
    - data: словарь с данными новой строки {column: value, ...}
    """
    excel_file = ExcelFile.query.filter_by(id=file_id, user_id=current_user.id, is_active=True).first_or_404()
    
    # Проверяем права доступа
    if not can_perform_action(excel_file, 'write'):
        return jsonify({
            'success': False,
            'error': 'У вас нет прав на изменение данного файла'
        }), 403
    
    data = request.json
    
    if not data or 'data' not in data:
        return jsonify({
            'success': False,
            'error': 'Отсутствуют необходимые данные для новой строки'
        }), 400
        
    sheet_name = data.get('sheet')
    row_data = data['data']
    
    success, error = add_excel_row(excel_file.file_path, sheet_name, row_data)
    
    if not success:
        return jsonify({
            'success': False,
            'error': error
        }), 400
        
    return jsonify({
        'success': True,
        'message': 'Строка успешно добавлена'
    })

@bp.route('/excel/<int:file_id>/row/<int:row_index>', methods=['DELETE'])
@login_required
def delete_row(file_id, row_index):
    """
    API для удаления строки
    
    URL параметры:
    - row_index: индекс строки для удаления (начиная с 0)
    
    GET параметры:
    - sheet: имя листа (опционально)
    """
    excel_file = ExcelFile.query.filter_by(id=file_id, user_id=current_user.id, is_active=True).first_or_404()
    
    # Проверяем права доступа
    if not can_perform_action(excel_file, 'delete'):
        return jsonify({
            'success': False,
            'error': 'У вас нет прав на удаление данных в этом файле'
        }), 403
    
    sheet_name = request.args.get('sheet')
    
    success, error = delete_excel_row(excel_file.file_path, sheet_name, row_index)
    
    if not success:
        return jsonify({
            'success': False,
            'error': error
        }), 400
        
    return jsonify({
        'success': True,
        'message': 'Строка успешно удалена'
    })
