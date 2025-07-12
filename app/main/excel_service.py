import os
import pandas as pd
import json
from flask import current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from app.models import ExcelFile, PermissionMode

def modify_excel_data(file_path, sheet_name, row_index, col_name, new_value):
    """
    Изменяет значение ячейки в Excel-файле.
    
    Args:
        file_path: Путь к Excel-файлу
        sheet_name: Имя листа
        row_index: Индекс строки (начиная с 0)
        col_name: Имя колонки
        new_value: Новое значение
    
    Returns:
        tuple: (success, error)
    """
    try:
        # Проверяем существование файла
        if not os.path.exists(file_path):
            return False, "Файл не найден"
            
        # Загружаем данные
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            # Если имя листа не указано, используем первый лист
            df = pd.read_excel(file_path)
        
        # Проверяем, что индекс строки и имя колонки существуют
        if row_index >= len(df) or col_name not in df.columns:
            return False, "Указанная ячейка не существует"
        
        # Изменяем значение
        df.at[row_index, col_name] = new_value
        
        # Сохраняем файл
        with pd.ExcelWriter(file_path, mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
        return True, None
    except Exception as e:
        current_app.logger.error(f"Error modifying Excel data: {str(e)}")
        return False, f"Failed to modify Excel data: {str(e)}"

def add_excel_row(file_path, sheet_name, new_row_data):
    """
    Добавляет новую строку в Excel-файл.
    
    Args:
        file_path: Путь к Excel-файлу
        sheet_name: Имя листа
        new_row_data: Словарь с данными новой строки {column_name: value}
    
    Returns:
        tuple: (success, error)
    """
    try:
        # Проверяем существование файла
        if not os.path.exists(file_path):
            return False, "Файл не найден"
            
        # Загружаем данные
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(file_path)
        
        # Проверяем, что все колонки в new_row_data существуют в DataFrame
        for col in new_row_data.keys():
            if col not in df.columns:
                return False, f"Колонка {col} не существует в таблице"
        
        # Создаем новую строку с правильными колонками
        new_row = {}
        for col in df.columns:
            new_row[col] = new_row_data.get(col, None)
        
        # Добавляем строку
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Сохраняем файл
        with pd.ExcelWriter(file_path, mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
        return True, None
    except Exception as e:
        current_app.logger.error(f"Error adding Excel row: {str(e)}")
        return False, f"Failed to add Excel row: {str(e)}"

def delete_excel_row(file_path, sheet_name, row_index):
    """
    Удаляет строку из Excel-файла.
    
    Args:
        file_path: Путь к Excel-файлу
        sheet_name: Имя листа
        row_index: Индекс строки для удаления (начиная с 0)
    
    Returns:
        tuple: (success, error)
    """
    try:
        # Проверяем существование файла
        if not os.path.exists(file_path):
            return False, "Файл не найден"
            
        # Загружаем данные
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(file_path)
        
        # Проверяем, что индекс строки существует
        if row_index >= len(df):
            return False, "Строка с указанным индексом не существует"
        
        # Удаляем строку
        df = df.drop(row_index).reset_index(drop=True)
        
        # Сохраняем файл
        with pd.ExcelWriter(file_path, mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
        return True, None
    except Exception as e:
        current_app.logger.error(f"Error deleting Excel row: {str(e)}")
        return False, f"Failed to delete Excel row: {str(e)}"

def can_perform_action(excel_file, action_type):
    """
    Проверяет, можно ли выполнить действие с файлом, в зависимости от уровня доступа.
    
    Args:
        excel_file: Объект ExcelFile
        action_type: Тип действия ('read', 'write', 'delete')
    
    Returns:
        bool: True, если действие разрешено
    """
    if action_type == 'read':
        return excel_file.permission_mode in [PermissionMode.READ, PermissionMode.READ_WRITE, PermissionMode.READ_WRITE_DELETE]
    elif action_type == 'write':
        return excel_file.permission_mode in [PermissionMode.READ_WRITE, PermissionMode.READ_WRITE_DELETE]
    elif action_type == 'delete':
        return excel_file.permission_mode == PermissionMode.READ_WRITE_DELETE
    else:
        return False
