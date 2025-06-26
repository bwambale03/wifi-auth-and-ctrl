from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from app.models.admin import Admin
from app.models.exclusion import Exclusion
from app.models.transaction import Transaction
from app.models.user import User
from app.extensions import db
import logging
from datetime import timedelta
import pyotp
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Step 1: Verify username/password and return a temporary token."""
    try:
        data = request.get_json(silent=True)
        if not data or not data.get('username') or not data.get('password'):
            logger.warning("Admin login attempt failed: Missing username or password")
            return jsonify({"error": "Username and password are required"}), 400
        # # debug logging
        # current_app.logger.debug(f"Admin login attempt: username={data['username']}, password={data['password']}")
        
        
        #  # Verify with 1-minute window (typical TOTP allows ±30 seconds)
        # totp = pyotp.TOTP(admin.otp_secret)
        # if not totp.verify(data['totp_code'], valid_window=1):
        #     current_app.logger.warning(f"TOTP verification failed for admin: {admin.username}")
        #     return jsonify({"error": "Invalid TOTP code"}), 401
        
        admin = Admin.query.filter_by(username=data['username']).first()
        if not admin:
            logger.warning(f"Admin login attempt failed: Admin not found for username={data['username']}")
            return jsonify({"error": "Invalid credentials"}), 401
        if not admin.check_password(data['password']):
            logger.warning(f"Admin login attempt failed: Invalid password for username={data['username']}")
            return jsonify({"error": "Invalid credentials"}), 401

        # Generate a temporary token for TOTP verification
        temp_token = create_access_token(identity=admin.id, expires_delta=timedelta(minutes=5))
        logger.info(f"Admin login attempt: Username/password verified for username={admin.username}, temp token issued")
        return jsonify({"message": "Username and password verified", "temp_token": temp_token}), 200
    except BadRequest:
        logger.error("Admin login error: Invalid JSON payload")
        return jsonify({"error": "Invalid JSON payload"}), 400
    except SQLAlchemyError as e:
        logger.error(f"Admin login error: Database error - {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logger.error(f"Admin login error: Unexpected error - {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    
    

@admin_bp.route('/verify-totp', methods=['POST'])
@jwt_required()
def verify_totp():
    """Step 2: Verify TOTP code and issue final admin token."""
    try:
        # CHANGED: Simplified JWT identity extraction
        admin = Admin.query.get(get_jwt_identity())
        if not admin:
            logger.warning(f"Admin TOTP verification failed: Admin not found")
            return jsonify({"error": "Admin not found"}), 404

        # CHANGED: Removed silent=True for stricter JSON parsing
        data = request.get_json()
        if not data or not data.get('totp_code'):
            logger.warning("Admin TOTP verification failed: Missing TOTP code")
            return jsonify({"error": "TOTP code is required"}), 400

        totp_code = data['totp_code'].strip()
        logger.debug(f"Verifying TOTP for {admin.username}")
        
        if not admin.otp_secret:
            logger.error("Admin TOTP verification failed: No TOTP secret set")
            return jsonify({"error": "TOTP not configured"}), 500
            
        if not admin.verify_totp(totp_code):
            logger.warning("Admin TOTP verification failed: Invalid code")
            return jsonify({"error": "Invalid TOTP code"}), 401

        # CHANGED: Return both token and CSRF in JSON response
        access_token = create_access_token(
            identity=admin.id,
            expires_delta=timedelta(days=1),
            additional_claims={"is_admin": True}
        )
        
        response_data = {
            "message": "Login successful",
            "admin": admin.to_dict(),
            "access_token": access_token,  # CHANGED: Added token to response body
            "csrf_token": get_jwt()["csrf"]  # CHANGED: Explicit CSRF return
        }
        
        response = jsonify(response_data)
        
        # CHANGED: Maintain cookie setting for backward compatibility
        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=False,
            samesite='Strict',
            max_age=86400
        )
        
        return response, 200
        
    except BadRequest:
        logger.error("Invalid JSON payload in TOTP verification")
        return jsonify({"error": "Invalid request format"}), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error during TOTP verification: {str(e)}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in TOTP verification: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    

@admin_bp.route('/exclusions', methods=['GET'])
@jwt_required()
def get_exclusions():
    """Get all exclusions."""
    try:
        admin_id = get_jwt_identity()
        admin = Admin.query.get(admin_id)
        if not admin:
            logger.warning(f"Exclusions fetch failed: Admin not found for id={admin_id}")
            return jsonify({"error": "Admin not found"}), 404

        exclusions = Exclusion.query.all()
        return jsonify({"exclusions": [e.to_dict() for e in exclusions]}), 200
    except Exception as e:
        logger.error(f"Exclusions fetch error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@admin_bp.route('/exclusions', methods=['POST'])
@jwt_required()
def add_exclusion():
    """Add a new exclusion."""
    try:
        admin_id = get_jwt_identity()
        admin = Admin.query.get(admin_id)
        if not admin:
            logger.warning(f"Exclusion add failed: Admin not found for id={admin_id}")
            return jsonify({"error": "Admin not found"}), 404

        data = request.get_json()
        if not data or not data.get('type') or not data.get('value'):
            logger.warning(f"Exclusion add failed: Missing type or value for admin={admin.username}")
            return jsonify({"error": "Type and value are required"}), 400

        exclusion = Exclusion(
            type=data['type'],
            value=data['value'],
            reason=data.get('reason'),
            exclude_from_payment=data.get('exclude_from_payment', False),
            exclude_from_connection=data.get('exclude_from_connection', False)
        )
        db.session.add(exclusion)
        db.session.commit()
        logger.info(f"Exclusion added: type={exclusion.type}, value={exclusion.value}, admin={admin.username}")
        return jsonify(exclusion.to_dict()), 201
    except Exception as e:
        logger.error(f"Exclusion add error: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@admin_bp.route('/exclusions/<int:exclusion_id>', methods=['DELETE'])
@jwt_required()
def delete_exclusion(exclusion_id):
    """Delete an exclusion."""
    try:
        admin_id = get_jwt_identity()
        admin = Admin.query.get(admin_id)
        if not admin:
            logger.warning(f"Exclusion delete failed: Admin not found for id={admin_id}")
            return jsonify({"error": "Admin not found"}), 404

        exclusion = Exclusion.query.get(exclusion_id)
        if not exclusion:
            logger.warning(f"Exclusion delete failed: Exclusion not found for id={exclusion_id}, admin={admin.username}")
            return jsonify({"error": "Exclusion not found"}), 404

        db.session.delete(exclusion)
        db.session.commit()
        logger.info(f"Exclusion deleted: id={exclusion_id}, admin={admin.username}")
        return jsonify({"message": "Exclusion deleted"}), 200
    except Exception as e:
        logger.error(f"Exclusion delete error: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@admin_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """Get all transactions."""
    try:
        admin_id = get_jwt_identity()
        admin = Admin.query.get(admin_id)
        if not admin:
            logger.warning(f"Transactions fetch failed: Admin not found for id={admin_id}")
            return jsonify({"error": "Admin not found"}), 404

        transactions = Transaction.query.all()
        return jsonify({"transactions": [t.to_dict() for t in transactions]}), 200
    except Exception as e:
        logger.error(f"Transactions fetch error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users."""
    try:
        admin_id = get_jwt_identity()
        admin = Admin.query.get(admin_id)
        if not admin:
            logger.warning(f"Users fetch failed: Admin not found for id={admin_id}")
            return jsonify({"error": "Admin not found"}), 404

        users = User.query.all()
        return jsonify({"users": [u.to_dict() for u in users]}), 200
    except Exception as e:
        logger.error(f"Users fetch error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    
@admin_bp.route('/me', methods=['GET'])
@jwt_required()
def get_admin():
    """Get current admin's details."""
    admin_id = get_jwt_identity()
    admin = Admin.query.get(admin_id)
    if not admin:
        logger.warning(f"Admin fetch failed: admin_id={admin_id}")
        return jsonify({"error": "Admin not found"}), 404

    logger.info(f"Current admin fetched: admin_id={admin_id}")
    return jsonify({"admin": admin.to_dict()}), 200