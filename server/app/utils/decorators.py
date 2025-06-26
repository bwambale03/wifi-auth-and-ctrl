from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User, Transaction
from datetime import datetime
import logging

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def payment_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = None
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
        except Exception:
            pass

        phone_number = request.args.get('phone_number') or \
                       (User.query.get(user_id).phone_number if user_id else None)

        if not phone_number:
            return jsonify({"error": "Phone number required"}), 400

        transaction = Transaction.query.filter_by(
            phone_number=phone_number,
            status='SUCCESSFUL'
        ).filter(
            Transaction.expiry > datetime.utcnow()
        ).first()

        if not transaction:
            return jsonify({"error": "No active package found"}), 403

        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # 1. Verify JWT first
            verify_jwt_in_request()
            
            # 2. Get user
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            # 3. Validate admin status
            if not user or not user.is_admin:
                logger.warning(f"Admin access denied for user_id={user_id}")
                return jsonify({
                    "error": "Administrator privileges required",
                    "code": "ADMIN_ACCESS_DENIED"
                }), 403
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Admin check failed: {str(e)}")
            return jsonify({
                "error": "Authorization verification failed",
                "code": "AUTH_VERIFICATION_ERROR"
            }), 401
            
    return decorated_function