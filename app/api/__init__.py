from flask import Blueprint

bp = Blueprint('api', __name__)

from app.api import routes, excel_api, ai_actions, voice_api
