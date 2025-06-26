from flask import request, jsonify, current_app, Blueprint, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.extensions import db
import logging
import re
import random
import string
from datetime import timedelta, datetime
import pytz
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException  # NEW: Import for Twilio error handling

# Set up logging
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Initialize Limiter
limiter = Limiter(
    get_remote_address,
    app=current_app,
    default_limits=["200 per day", "50 per hour"]
)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user with phone number and optional email/password."""
    data = request.get_json()
    
    # Input validation
    if not data or not data.get('phone_number'):
        logger.warning("Registration failed: Missing phone number")
        return jsonify({"error": "Phone number is required"}), 400

    phone_number = data.get('phone_number')
    email = data.get('email')
    password = data.get('password')

    # Validate phone number format
    if not re.match(r'^\+\d{10,15}$', phone_number):
        logger.warning(f"Registration failed: Invalid phone number format: {phone_number}")
        return jsonify({"error": "Invalid phone number format"}), 400

    # Validate email if provided
    if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        logger.warning(f"Registration failed: Invalid email format: {email}")
        return jsonify({"error": "Invalid email format"}), 400

    # Validate password if provided
    if password and len(password) < 8:
        logger.warning("Registration failed: Password too short")
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    # Check for existing user
    existing_user = User.query.filter(
        (User.phone_number == phone_number) | (User.email == email)
    ).first()
    if existing_user:
        logger.warning(f"Registration failed: Duplicate found - phone_number={phone_number}, email={email}")
        return jsonify({"error": "Phone number or email already exists"}), 409

    logger.info(f"Attempting registration: phone_number={phone_number}, email={email}")

    # Database operations
    try:
        user = User(
            phone_number=phone_number,
            email=email,
            is_phone_verified=not data.get('is_admin', False),  # True for non-admins, False for admins
            is_admin=data.get('is_admin', False)
        )
        if password:
            user.set_password(password)
        db.session.add(user)
        db.session.commit()
        logger.info(f"User registered successfully: phone_number={phone_number}")
        return jsonify({"message": "Registration successful"}), 201
        
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Registration failed: IntegrityError - phone_number={phone_number}, email={email}, error={str(e)}")
        return jsonify({"error": "Phone number or email already exists"}), 409
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration failed: Unexpected error - phone_number={phone_number}, email={email}, error={str(e)}")
        return jsonify({"error": "Registration failed", "details": str(e)}), 500
    
    
    

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Log in a user with phone number or email and password."""
    data = request.get_json()
    
    # Input validation
    if not data or not (data.get('phone_number') or data.get('email')) or not data.get('password'):
        logger.warning("Login failed: Missing credentials")
        return jsonify({"error": "Phone number or email and password are required"}), 400

    identifier = data.get('phone_number') or data.get('email')
    password = data.get('password')

    # Find user by phone or email
    user = User.query.filter(
        (User.phone_number == identifier) | (User.email == identifier)
    ).first()

    # Authentication check
    if not user or not user.check_password(password):
        logger.warning(f"Login failed: Invalid credentials for {identifier}")
        return jsonify({"error": "Invalid phone number or password"}), 401

    # Skip phone verification for non-admin users
    if user.is_admin and not user.is_phone_verified:
        logger.warning(f"Login failed: Phone not verified for admin {identifier}")
        return jsonify({"error": "Phone number not verified"}), 403

    try:
        # Generate JWT token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(days=1)
        )
        response = jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "phone_number": user.phone_number,
                "email": user.email,
                "is_phone_verified": user.is_phone_verified
            }
        })
        
        logger.info(f"User logged in: user_id={user.id}")
        return response, 200
    except Exception as e:
        logger.error(f"Login error: identifier={identifier}, error={str(e)}")
        return jsonify({"error": "Server error"}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Log out a user."""
    logger.info("User logged out")
    return jsonify({"message": "Logout successful"}), 200


from datetime import datetime, timezone
import pytz

@auth_bp.route('/verify-phone', methods=['POST'])
def verify_phone():
    data = request.get_json()
    if not data or not data.get('phone_number'):
        logger.warning("Phone verification failed: Missing phone number")
        return jsonify({"error": "Phone number is required"}), 400

    phone_number = data.get('phone_number')
    if not re.match(r'^\+\d{10,15}$', phone_number):
        logger.warning(f"Phone verification failed: Invalid phone number format: {phone_number}")
        return jsonify({"error": "Invalid phone number format"}), 400

    otp = ''.join(random.choices(string.digits, k=6))
    logger.info(f"OTP generated for {phone_number}: {otp}")
    
    # NEW: Correct Twilio client initialization and add error handling
    try:
        client = Client(
            current_app.config['TWILIO_ACCOUNT_SID'],
            current_app.config['TWILIO_AUTH_TOKEN']
        )
        message = client.messages.create(
            body=f"Your OTP is {otp}",
            from_=current_app.config['TWILIO_PHONE_NUMBER'],
            to=phone_number
        )
        logger.info(f"OTP sent to {phone_number}: {message.sid}")
    except TwilioRestException as e:
        logger.error(f"Twilio error: phone={phone_number}, error={str(e)}")
        return jsonify({"error": "Failed to send OTP", "details": str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in Twilio: phone={phone_number}, error={str(e)}")
        return jsonify({"error": "Failed to send OTP", "details": str(e)}), 500

    try:
        user = User.query.filter_by(phone_number=phone_number).first()
        if not user:
            user = User(phone_number=phone_number)
            db.session.add(user)
        user.otp = otp
        user.otp_expiry = datetime.now(pytz.timezone('Africa/Kampala')) + timedelta(minutes=5)
        db.session.commit()
        return jsonify({"message": "OTP sent successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Phone verification failed: phone={phone_number}, error={str(e)}")
        return jsonify({"error": "Server error during phone verification", "details": str(e)}), 500
    

@auth_bp.route('/confirm-otp', methods=['POST'])
def confirm_otp():
    data = request.get_json()
    if not data or not data.get('phone_number') or not data.get('otp'):
        logger.warning("OTP confirmation failed: Missing phone number or OTP")
        return jsonify({"error": "Phone number and OTP are required"}), 400

    phone_number = data.get('phone_number')
    otp = data.get('otp')

    try:
        user = User.query.filter_by(phone_number=phone_number).first()
        logger.info(f"User found: {user}, OTP: {user.otp}, Expiry: {user.otp_expiry}")
        if not user:
            logger.warning(f"OTP confirmation failed: User not found for {phone_number}")
            return jsonify({"error": "User not found"}), 404
        if user.otp != otp:
            logger.warning(f"OTP confirmation failed: Invalid OTP for {phone_number}")
            return jsonify({"error": "Invalid OTP"}), 401
        # Convert offset-naive otp_expiry to offset-aware
        kampala_tz = pytz.timezone('Africa/Kampala')
        expiry_aware = kampala_tz.localize(user.otp_expiry)
        if expiry_aware < datetime.now(kampala_tz):
            logger.warning(f"OTP confirmation failed: Expired OTP for {phone_number}")
            return jsonify({"error": "Expired OTP"}), 401

        logger.info(f"Updating user: otp=None, otp_expiry=None, is_phone_verified=True")
        user.otp = None
        user.otp_expiry = None
        user.is_phone_verified = True
        db.session.commit()
        logger.info(f"Phone verified: phone={phone_number}")
        return jsonify({"message": "Phone number verified successfully"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"OTP confirmation failed: phone={phone_number}, error={str(e)}")
        return jsonify({"error": "Server error during OTP confirmation", "details": str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_user():
    """Get current user's details."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        logger.warning(f"User fetch failed: user_id={user_id}")
        return jsonify({"error": "User not found"}), 404

    logger.info(f"current user fetched: user_id={user_id}")
    return jsonify({"user": user.to_dict()}), 200


# In auth.py, add this endpoint within the auth_bp Blueprint
@auth_bp.route('/check-user', methods=['POST'])
def check_user():
    """Check if a user exists by phone number."""
    data = request.get_json()
    if not data or not data.get('phone_number'):
        logger.warning("Check user failed: Missing phone number")
        return jsonify({"error": "Phone number is required"}), 400

    phone_number = data.get('phone_number')
    if not re.match(r'^\+\d{10,15}$', phone_number):
        logger.warning(f"Check user failed: Invalid phone number format: {phone_number}")
        return jsonify({"error": "Invalid phone number format"}), 400

    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        logger.info(f"User not found: phone={phone_number}")
        return jsonify({"exists": False}), 404
    logger.info(f"User found: phone={phone_number}, verified={user.is_phone_verified}")
    return jsonify({"exists": True, "is_phone_verified": user.is_phone_verified}), 200
