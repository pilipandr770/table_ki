from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, SubmitField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, Optional
from flask_babel import lazy_gettext as _l
from app.models import PermissionMode

class FileUploadForm(FlaskForm):
    file = FileField(_l('Excel File'), validators=[
        FileRequired(message=_l('Please select a file')),
        FileAllowed(['xlsx', 'xls'], message=_l('Only Excel files are allowed'))
    ])
    permission_mode = SelectField(
        _l('Permission Mode'),
        choices=[
            (PermissionMode.READ.value, _l('Read Only')),
            (PermissionMode.READ_WRITE.value, _l('Read & Write')),
            (PermissionMode.READ_WRITE_DELETE.value, _l('Full Access'))
        ],
        default=PermissionMode.READ.value,
        validators=[DataRequired()]
    )
    submit = SubmitField(_l('Upload File'))

class ChatForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[DataRequired(), Length(max=1000)])
    session_id = HiddenField()
    submit = SubmitField(_l('Send'))

class NewChatSessionForm(FlaskForm):
    session_name = StringField(_l('Session Name'), validators=[Optional(), Length(max=255)])
    excel_file_id = SelectField(_l('Excel File'), coerce=int, validators=[DataRequired()])
    submit = SubmitField(_l('Start Chat Session'))

class EditFilePermissionForm(FlaskForm):
    permission_mode = SelectField(
        _l('Permission Mode'),
        choices=[
            (PermissionMode.READ.value, _l('Read Only')),
            (PermissionMode.READ_WRITE.value, _l('Read & Write')),
            (PermissionMode.READ_WRITE_DELETE.value, _l('Full Access'))
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField(_l('Update Permissions'))
