from flask import Blueprint

bp = Blueprint('audio_test', __name__)

from app.audio_test import routes
