from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from flask_babel import lazy_gettext as _l
from app.models import User

class LoginForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))

class RegistrationForm(FlaskForm):
    first_name = StringField(_l('First Name'), validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField(_l('Last Name'), validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        _l('Repeat Password'), 
        validators=[DataRequired(), EqualTo('password', message=_l('Passwords must match'))]
    )
    language_preference = SelectField(
        _l('Preferred Language'),
        choices=[('en', 'English'), ('de', 'Deutsch'), ('ru', 'Русский')],
        default='en',
        validators=[DataRequired()]
    )
    submit = SubmitField(_l('Register'))
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError(_l('Email address is already registered.'))

class SubscriptionForm(FlaskForm):
    plan_type = SelectField(
        _l('Subscription Plan'),
        choices=[('single-table', _l('Single Table Plan')), ('multi-table', _l('Multi Table Plan'))],
        validators=[DataRequired()]
    )
    submit = SubmitField(_l('Subscribe'))

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(_l('Current Password'), validators=[DataRequired()])
    new_password = PasswordField(_l('New Password'), validators=[DataRequired(), Length(min=6)])
    new_password2 = PasswordField(
        _l('Repeat New Password'),
        validators=[DataRequired(), EqualTo('new_password', message=_l('Passwords must match'))]
    )
    submit = SubmitField(_l('Change Password'))

class ProfileForm(FlaskForm):
    first_name = StringField(_l('First Name'), validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField(_l('Last Name'), validators=[DataRequired(), Length(min=2, max=50)])
    language_preference = SelectField(
        _l('Preferred Language'),
        choices=[('en', 'English'), ('de', 'Deutsch'), ('ru', 'Русский')],
        validators=[DataRequired()]
    )
    submit = SubmitField(_l('Update Profile'))
