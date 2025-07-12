from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from app import db, login_manager
import enum

class UserRole(enum.Enum):
    USER = 'user'
    ADMIN = 'admin'

class SubscriptionStatus(enum.Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    CANCELLED = 'cancelled'
    PAST_DUE = 'past_due'

class PlanType(enum.Enum):
    SINGLE_TABLE = 'single-table'
    MULTI_TABLE = 'multi-table'

class PermissionMode(enum.Enum):
    READ = 'read'
    READ_WRITE = 'read_write'
    READ_WRITE_DELETE = 'read_write_delete'

class MessageType(enum.Enum):
    TEXT = 'text'
    VOICE = 'voice'
    SYSTEM = 'system'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    language_preference = db.Column(db.String(2), default='en', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    subscription = db.relationship('Subscription', backref='user', uselist=False, cascade='all, delete-orphan')
    excel_files = db.relationship('ExcelFile', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    chat_sessions = db.relationship('ChatSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def can_access_system(self):
        # Администраторы имеют полный доступ без подписки
        if self.is_admin():
            return True
        return self.is_approved and (self.subscription and self.subscription.is_active())
    
    def can_upload_files(self):
        # Администраторы могут загружать неограниченное количество файлов
        if self.is_admin():
            return True, 999  # Практически неограниченно
            
        if not self.can_access_system():
            return False, 0
        
        max_files = self.subscription.plan_type.value if self.subscription else 0
        # Конвертируем plan_type в числовое значение файлов
        if max_files == 'single-table':
            max_files = 1
        elif max_files == 'multi-table':
            max_files = 10
        else:
            max_files = 0
            
        current_files = self.excel_files.filter_by(is_active=True).count()
        
        return current_files < max_files, max_files - current_files
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    plan_type = db.Column(db.Enum(PlanType), nullable=False)
    status = db.Column(db.Enum(SubscriptionStatus), default=SubscriptionStatus.INACTIVE, nullable=False)
    stripe_subscription_id = db.Column(db.String(255), unique=True)
    stripe_customer_id = db.Column(db.String(255))
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def plan(self):
        from flask import current_app
        return current_app.config['SUBSCRIPTION_PLANS'].get(self.plan_type.value, {})
    
    def is_active(self):
        return (self.status == SubscriptionStatus.ACTIVE and 
                self.current_period_end and 
                self.current_period_end > datetime.utcnow())
    
    def days_until_expiry(self):
        if self.current_period_end:
            return (self.current_period_end - datetime.utcnow()).days
        return 0
    
    def __repr__(self):
        return f'<Subscription {self.user_id}:{self.plan_type.value}>'

class ExcelFile(db.Model):
    __tablename__ = 'excel_files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    permission_mode = db.Column(db.Enum(PermissionMode), default=PermissionMode.READ, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # File metadata
    sheet_names = db.Column(db.Text)  # JSON string of sheet names
    row_count = db.Column(db.Integer)
    column_count = db.Column(db.Integer)
    
    # Relationships
    chat_sessions = db.relationship('ChatSession', backref='excel_file', lazy='dynamic', cascade='all, delete-orphan')
    
    def can_read(self):
        """Проверяет, есть ли у пользователя права на чтение файла"""
        return self.permission_mode in [PermissionMode.READ, PermissionMode.READ_WRITE, PermissionMode.READ_WRITE_DELETE]
    
    def can_write(self):
        """Проверяет, есть ли у пользователя права на запись в файл"""
        return self.permission_mode in [PermissionMode.READ_WRITE, PermissionMode.READ_WRITE_DELETE]
    
    def can_delete(self):
        """Проверяет, есть ли у пользователя права на удаление данных в файле"""
        return self.permission_mode == PermissionMode.READ_WRITE_DELETE
    
    def get_permission_mode_display(self):
        """Возвращает читаемое название режима доступа"""
        if self.permission_mode == PermissionMode.READ:
            return "Только чтение"
        elif self.permission_mode == PermissionMode.READ_WRITE:
            return "Чтение и запись"
        elif self.permission_mode == PermissionMode.READ_WRITE_DELETE:
            return "Полный доступ"
        return "Неизвестно"
    
    def can_read(self):
        return self.permission_mode in [PermissionMode.READ, PermissionMode.READ_WRITE, PermissionMode.READ_WRITE_DELETE]
    
    def can_write(self):
        return self.permission_mode in [PermissionMode.READ_WRITE, PermissionMode.READ_WRITE_DELETE]
    
    def can_delete(self):
        return self.permission_mode == PermissionMode.READ_WRITE_DELETE
    
    def get_file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)
    
    def __repr__(self):
        return f'<ExcelFile {self.filename}>'

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    excel_file_id = db.Column(db.Integer, db.ForeignKey('excel_files.id'), nullable=False)
    session_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    messages = db.relationship('ChatMessage', backref='session', lazy='dynamic', cascade='all, delete-orphan', order_by='ChatMessage.timestamp')
    
    def get_message_count(self):
        return self.messages.count()
    
    def get_last_message(self):
        return self.messages.order_by(ChatMessage.timestamp.desc()).first()
    
    def __repr__(self):
        return f'<ChatSession {self.id}>'

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False)
    message_type = db.Column(db.Enum(MessageType), nullable=False)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(2), nullable=False)
    is_user_message = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # For voice messages
    audio_file_path = db.Column(db.String(500))
    transcription = db.Column(db.Text)
    
    # For system messages and additional data
    extra_data = db.Column(db.Text)  # JSON string for additional data
    
    def is_from_user(self):
        return self.is_user_message
    
    def is_from_assistant(self):
        return not self.is_user_message
    
    def __repr__(self):
        return f'<ChatMessage {self.id}:{self.message_type.value}>'
