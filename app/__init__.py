import os
import logging
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
from flasgger import Swagger
from .models import db, User
from .email_utils import mail
from .analytics_routes import analytics_bp
from .admin_routes import admin_bp
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    load_dotenv()
    
    app = Flask(__name__, 
                template_folder='../templates', 
                static_folder='../static')
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')
    
    # Database Configuration (Neon PostgreSQL)
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
    
    if not database_url:
        logger.error("CRITICAL: No DATABASE_URL or POSTGRES_URL found in environment!")
        # On local development with no ENV, we still raise error to prevent accidental SQLite use
        raise RuntimeError("Database connection string (DATABASE_URL) is required for Neon PostgreSQL.")

    # Fix for PostgreSQL: Vercel/Heroku provide 'postgres://' which SQLAlchemy 1.4+ needs as 'postgresql://'
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Session & Cookie Security (Hardened for Serverless)
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600 # 1 hour

    # Mail Configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'AI Bug Tracker <noreply@gmail.com>')
    app.config['MAIL_DEBUG'] = True
    app.config['ADMIN_PASSWORD_HASH'] = os.environ.get('ADMIN_PASSWORD_HASH')

    db.init_app(app)
    mail.init_app(app)
    
    # Swagger - only initialize if not in a Vercel function (optional, helps startup)
    if not os.environ.get('VERCEL') or os.environ.get('ENABLE_SWAGGER') == 'True':
        Swagger(app)
    else:
        logger.info("Skipping Swagger initialization for faster cold start.")

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import main_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)

    # Automatically create tables in the database (Neon PostgreSQL)
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database tables: {str(e)}")

    return app
