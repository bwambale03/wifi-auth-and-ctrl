from flask import Flask, request, jsonify, current_app
import requests
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy.exc import OperationalError
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from app.commands import init_commands  # Add this import

from app.extensions import db
from app.models.user import User
from app.models.transaction import Transaction
from app.routes.admin import admin_bp
from app.routes.auth import auth_bp
from app.routes.payments import payments_bp


# Initialize extensions
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv('RATELIMIT_STORAGE_URL', 'memory://') if os.getenv('FLASK_ENV') != 'production' else 'redis://localhost:6379',
    strategy='fixed-window'
)

def create_app():
    """Factory function to create and configure the Flask app."""
    app = Flask(__name__)

    # Load environment variables
    load_dotenv()

    # Configuration
    app.config.from_object('app.config.Config')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config['JWT_TOKEN_LOCATION'] = ['headers','cookies']
    app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
    app.config['JWT_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
    app.config['JWT_COOKIE_SAMESITE'] = 'Strict'
    app.config['JWT_HEADER_CSRF_PROTECT'] = True
    app.config['JWT_ACCESS_CSRF_HEADER_NAME'] = 'X-CSRF-TOKEN'
    
    app.config['TWILIO_ACCOUNT_SID'] = os.getenv('TWILIO_ACCOUNT_SID')
    app.config['TWILIO_AUTH_TOKEN'] = os.getenv('TWILIO_AUTH_TOKEN')
    app.config['TWILIO_PHONE_NUMBER'] = os.getenv('TWILIO_PHONE_NUMBER')
    app.config['RATELIMIT_STORAGE_URL'] = 'redis://localhost:6379' if os.getenv('FLASK_ENV') == 'production' else 'memory://'
    # app.config['CORS_HEADERS'] = 'Content-Type, Authorization'

    # Override database URI with environment variables
    if os.getenv('DATABASE_URI'):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    elif os.getenv('DEV_DATABASE_URI'):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DEV_DATABASE_URI')

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    CORS(app, supports_credentials=True, resources={
            r"/api/*": {
                "origins": ["http://localhost:3000"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-CSRF-TOKEN"]
            }
        })
    
    # Register commands - this should come AFTER db initialization
    init_commands(app)  # This registers all your CLI commands
    # Set up logging
    if not app.debug:
        handler = RotatingFileHandler('server.log', maxBytes=100000, backupCount=3)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Internet Portal startup')

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # Scheduler task to check for expired transactions
    def check_expired_transactions():
        with app.app_context():
            expired_transactions = Transaction.query.filter(
                Transaction.status == 'SUCCESSFUL',
                Transaction.expiry <= datetime.utcnow()
            ).all()
            for tx in expired_transactions:
                app.logger.info(f"Transaction expired: transaction_id={tx.transaction_id}, phone_number={tx.phone_number}")
                disconnect_user(tx.phone_number)
                tx.status = 'EXPIRED'
                db.session.commit()

    # Initialize and start the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_expired_transactions, 'interval', minutes=1)
    scheduler.start()

    # Database initialization
    with app.app_context():
        try:
            if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
                db.engine.connect()
                app.logger.info("Connected to PostgreSQL database")
            db.create_all()
        except OperationalError as e:
            app.logger.error(f"Database connection failed: {str(e)}")
            app.logger.error("""
                PostgreSQL database might not exist. Create it with:
                sudo -u postgres createdb your_db_name
                Then verify permissions for your application user""")

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500
    
    @app.route('/debug/jwt-config')
    def debug_jwt_config():
        return jsonify({
            'jwt_secret': current_app.config['JWT_SECRET_KEY'],
            'secret_length': len(current_app.config['JWT_SECRET_KEY']) if current_app.config['JWT_SECRET_KEY'] else 0
        })
        
    @app.route('/debug/cors', methods=['GET', 'OPTIONS'])
    def debug_cors():
        return jsonify({"message": "CORS test"}), 200

    return app

def disconnect_user(phone_number):
    """Placeholder function to disconnect user from Wi-Fi."""
    current_app.logger.info(f"Disconnecting user: phone_number={phone_number}")
    # TODO: Implement Wi-Fi disconnection logic here

def payment_required(f):
    """Decorator to ensure user has an active package."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = None
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
        except:
            pass

        phone_number = request.args.get('phone_number') or (User.query.get(user_id).phone_number if user_id else None)
        if not phone_number:
            return jsonify({"error": "Phone number required"}), 400

        transaction = Transaction.query.filter_by(phone_number=phone_number, status='SUCCESSFUL').filter(Transaction.expiry > datetime.utcnow()).first()
        if not transaction:
            return jsonify({"error": "No active package found. Please purchase a package."}), 403

        return f(*args, **kwargs)
    return decorated_function

def register_commands(app):
    """Register CLI commands."""
    from flask_migrate import Migrate
    Migrate(app, db)
    
    
# Placeholder function to disconnect user from Wi-Fi
def disconnect_user(phone_number):
    current_app.logger.info(f"Disconnecting user: phone_number={phone_number}")
    try:
        # Example: Call a router API to disconnect the user
        # You may need to map phone_number to a MAC address or IP in your system
        response = requests.post(
            'http://router-ip:port/disconnect',
            json={'phone_number': phone_number},
            auth=('admin', 'password')  # Replace with your router credentials
        )
        response.raise_for_status()
        current_app.logger.info(f"User disconnected successfully: phone_number={phone_number}")
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to disconnect user: phone_number={phone_number}, error={str(e)}")
        
        
