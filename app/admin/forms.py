from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired, Optional
from flask_babel import lazy_gettext as _l
from app.models import UserRole, SubscriptionStatus, PlanType

class UserApprovalForm(FlaskForm):
    is_approved = BooleanField(_l('Approve User'))
    submit = SubmitField(_l('Update Approval Status'))

class UserRoleForm(FlaskForm):
    role = SelectField(
        _l('User Role'),
        choices=[(UserRole.USER.value, _l('User')), (UserRole.ADMIN.value, _l('Admin'))],
        validators=[DataRequired()]
    )
    submit = SubmitField(_l('Update Role'))

class SubscriptionStatusForm(FlaskForm):
    status = SelectField(
        _l('Subscription Status'),
        choices=[
            (SubscriptionStatus.ACTIVE.value, _l('Active')),
            (SubscriptionStatus.INACTIVE.value, _l('Inactive')),
            (SubscriptionStatus.CANCELLED.value, _l('Cancelled')),
            (SubscriptionStatus.PAST_DUE.value, _l('Past Due'))
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField(_l('Update Status'))

class AdminNoteForm(FlaskForm):
    note = TextAreaField(_l('Admin Note'), validators=[Optional()])
    submit = SubmitField(_l('Add Note'))
