from flask import Blueprint, render_template, send_from_directory, current_app
from flask_login import login_required
import os

# Create blueprint
audio_test_bp = Blueprint('audio_test', __name__)

@audio_test_bp.route('/')
@login_required
def audio_test():
    """Audio recording test page"""
    return send_from_directory(current_app.root_path, 'audio_test.html')
