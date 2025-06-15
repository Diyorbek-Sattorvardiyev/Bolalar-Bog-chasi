import os

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'very-hard-to-guess-secret-key'
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///kindergarten.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File uploads configuration
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads')
    ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # Application settings
    APP_NAME = "Bolalar Bog'chasi"
    TIMEZONE = 'Asia/Tashkent'