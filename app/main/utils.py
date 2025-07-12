import os
import pandas as pd
import json
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import current_app

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_user_upload_path(user_id):
    """Get the upload path for a specific user"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    user_folder = os.path.join(upload_folder, f"user_{user_id}")
    
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    
    return user_folder

def save_uploaded_file(file, user_id):
    """Save uploaded file and return file info"""
    if not file or not allowed_file(file.filename):
        return None, "Invalid file type"
    
    try:
        # Generate secure filename
        original_filename = file.filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        secure_name = secure_filename(original_filename)
        name, ext = os.path.splitext(secure_name)
        filename = f"{name}_{timestamp}{ext}"
        
        # Save file
        user_folder = get_user_upload_path(user_id)
        file_path = os.path.join(user_folder, filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Analyze Excel file
        file_info = analyze_excel_file(file_path)
        
        return {
            'filename': filename,
            'original_filename': original_filename,
            'file_path': file_path,
            'file_size': file_size,
            'sheet_names': json.dumps(file_info['sheet_names']),
            'row_count': file_info['row_count'],
            'column_count': file_info['column_count']
        }, None
        
    except Exception as e:
        current_app.logger.error(f"File upload error: {str(e)}")
        return None, f"File upload failed: {str(e)}"

def analyze_excel_file(file_path):
    """Analyze Excel file and return metadata"""
    try:
        # Read Excel file to get sheet names
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        # Get info from first sheet
        df = pd.read_excel(file_path, sheet_name=sheet_names[0])
        row_count = len(df)
        column_count = len(df.columns)
        
        return {
            'sheet_names': sheet_names,
            'row_count': row_count,
            'column_count': column_count
        }
    except Exception as e:
        current_app.logger.error(f"Excel analysis error: {str(e)}")
        return {
            'sheet_names': [],
            'row_count': 0,
            'column_count': 0
        }

def load_excel_data(file_path, sheet_name=None, max_rows=1000):
    """Load Excel data for display and analysis"""
    try:
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=max_rows)
        else:
            df = pd.read_excel(file_path, nrows=max_rows)
        
        # Convert to JSON for frontend
        data = {
            'columns': df.columns.tolist(),
            'data': df.fillna('').to_dict('records'),
            'total_rows': len(df),
            'dtypes': df.dtypes.astype(str).to_dict()
        }
        
        return data, None
    except Exception as e:
        current_app.logger.error(f"Excel loading error: {str(e)}")
        return None, f"Failed to load Excel data: {str(e)}"

def save_excel_data(file_path, data, sheet_name=None):
    """Save modified Excel data back to file"""
    try:
        # Convert data back to DataFrame
        df = pd.DataFrame(data)
        
        # Save to Excel
        if sheet_name:
            # Read existing file and update specific sheet
            with pd.ExcelWriter(file_path, mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            df.to_excel(file_path, index=False)
        
        return True, None
    except Exception as e:
        current_app.logger.error(f"Excel saving error: {str(e)}")
        return False, f"Failed to save Excel data: {str(e)}"

def get_excel_summary(file_path):
    """Get a summary of Excel file for chat assistant"""
    try:
        excel_file = pd.ExcelFile(file_path)
        summary = {
            'file_info': {
                'sheet_count': len(excel_file.sheet_names),
                'sheet_names': excel_file.sheet_names
            },
            'sheets': {}
        }
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=5)  # Sample first 5 rows
            
            summary['sheets'][sheet_name] = {
                'columns': df.columns.tolist(),
                'row_count': len(pd.read_excel(file_path, sheet_name=sheet_name)),
                'column_count': len(df.columns),
                'sample_data': df.fillna('').to_dict('records'),
                'dtypes': df.dtypes.astype(str).to_dict()
            }
        
        return summary, None
    except Exception as e:
        current_app.logger.error(f"Excel summary error: {str(e)}")
        return None, f"Failed to analyze Excel file: {str(e)}"

def delete_file(file_path):
    """Delete file from filesystem"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True, None
    except Exception as e:
        current_app.logger.error(f"File deletion error: {str(e)}")
        return False, f"Failed to delete file: {str(e)}"
