from flask import request, jsonify, current_app, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction import Transaction
from app.models.user import User
from app.utils.momo_api import MobileMoneyAPI
from app.extensions import db
from app.utils.decorators import payment_required
from app.models.access_code import AccessCode  # Add this import
from app.utils.code_generator import generate_random_code  # Add this import
import logging
import uuid
# CHANGED: Simplify datetime imports without aliasing
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)
payments_bp = Blueprint('payments', __name__)

# Mock package data (in production, store in database)
PACKAGES = [
    {"id": "1", "name": "1 Hour", "duration_hours": 1, "price": 0.5},
    {"id": "2", "name": "1 Day", "duration_hours": 24, "price": 2.0},
    {"id": "3", "name": "1 Week", "duration_hours": 168, "price": 10.0}
]

@payments_bp.route('/packages', methods=['GET'])
def get_packages():
    """List available internet packages."""
    logger.info("Fetching available packages")
    return jsonify({"packages": PACKAGES}), 200

from app.models.exclusion import Exclusion

@payments_bp.route('/initiate', methods=['POST'])
def initiate_payment():
    """Initiate a mobile money payment for a package."""
    try:
        data = request.get_json()
        if not data or not data.get('phone_number') or not data.get('package_id'):
            logger.warning("Payment initiation failed: Missing phone number or package ID")
            return jsonify({"error": "Phone number and package ID are required"}), 400

        phone_number = data.get('phone_number')
        package_id = data.get('package_id')

        # Check if phone number is excluded from payment
        exclusion = Exclusion.query.filter_by(type='PHONE', value=phone_number).first()
        if exclusion and exclusion.exclude_from_payment:
            # Skip payment and create a transaction directly
            transaction = Transaction(
                phone_number=phone_number,
                package_id=package_id,
                amount=0.0,  # Free for excluded users
                transaction_id=str(uuid.uuid4()),
                status='SUCCESSFUL'
            )
            package = next((p for p in PACKAGES if p['id'] == package_id), None)
            if package:
                # CHANGED: Use direct datetime and timedelta
                transaction.expiry = datetime.utcnow() + timedelta(hours=package['duration_hours'])
            transaction.completed_at = datetime.utcnow()
            db.session.add(transaction)
            db.session.commit()
            logger.info(f"Payment skipped for excluded user: phone={phone_number}, transaction_id={transaction.transaction_id}")
            return jsonify({
                "message": "Access granted without payment",
                "transaction_id": transaction.transaction_id,
                "status": transaction.status
            }), 200

        # Find package
        package = next((p for p in PACKAGES if p['id'] == package_id), None)
        if not package:
            logger.warning(f"Payment initiation failed: Invalid package ID: {package_id}")
            return jsonify({"error": "Invalid package ID"}), 404

        # Initialize mobile money API
        logger.debug("Initializing MobileMoneyAPI")
        momo_api = MobileMoneyAPI()

        # Initiate payment
        logger.debug(f"Initiating payment: phone={phone_number}, price={package['price']}, package_id={package_id}")
        result = momo_api.initiate_payment(phone_number, package['price'], package_id)
        if 'error' in result:
            logger.error(f"MobileMoneyAPI error: {result['error']}")
            return jsonify({"error": result['error']}), 500

        # Create transaction record
        logger.debug(f"Creating transaction: transaction_id={result['transaction_id']}")
        transaction = Transaction(
            phone_number=phone_number,
            package_id=package_id,
            amount=package['price'],
            transaction_id=result['transaction_id'],
            status=result['status']
        )
        db.session.add(transaction)
        db.session.commit()

        logger.info(f"Payment initiated: transaction_id={result['transaction_id']}, phone={phone_number}")
        return jsonify({
            "message": "Payment initiated",
            "transaction_id": result['transaction_id'],
            "status": result['status']
        }), 200

    except Exception as e:
        logger.error(f"Error in initiate_payment: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@payments_bp.route('/check-access', methods=['GET'])
@payment_required
def check_access():
    """Check if a user has access to the internet."""
    phone_number = request.args.get('phone_number')
    if not phone_number:
        return jsonify({"error": "Phone number required"}), 400

    # Check if phone number or MAC is excluded from connecting
    phone_exclusion = Exclusion.query.filter_by(type='PHONE', value=phone_number, exclude_from_connection=True).first()
    mac_address = request.args.get('mac_address')  # Optional: Pass MAC address if available
    mac_exclusion = Exclusion.query.filter_by(type='MAC', value=mac_address, exclude_from_connection=True).first() if mac_address else None

    if phone_exclusion or mac_exclusion:
        logger.info(f"Access denied due to exclusion: phone={phone_number}, mac={mac_address}")
        return jsonify({"error": "Access denied due to exclusion"}), 403

    return jsonify({"message": "Access granted"}), 200

@payments_bp.route('/verify/<transaction_id>', methods=['POST'])
def verify_payment(transaction_id):
    """Verify the status of a payment and activate package if successful."""
    transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
    if not transaction:
        logger.warning(f"Payment verification failed: Transaction not found: {transaction_id}")
        return jsonify({"error": "Transaction not found"}), 404

    # Initialize mobile money API
    momo_api = MobileMoneyAPI()

    # Verify payment
    result = momo_api.verify_payment(transaction_id)
    if 'error' in result:
        transaction.status = 'FAILED'
        db.session.commit()
        return jsonify(result), 500

    # Update transaction status
    transaction.status = result['status']
    if result['status'] == 'SUCCESSFUL':
        package = next((p for p in PACKAGES if p['id'] == transaction.package_id), None)
        if package:
            # CHANGED: Use direct datetime and timedelta
            transaction.expiry = datetime.utcnow() + timedelta(hours=package['duration_hours'])
        transaction.completed_at = datetime.utcnow()
    elif result['status'] == 'FAILED':
        # Attempt refund if payment failed
        refund_result = momo_api.refund_payment(transaction_id, transaction.amount)
        if 'error' in refund_result:
            logger.error(f"Refund failed for transaction: {transaction_id}")
        else:
            transaction.status = 'REFUNDED'

    db.session.commit()

    logger.info(f"Payment verified: transaction_id={transaction_id}, status={result['status']}")
    return jsonify({
        "transaction_id": transaction_id,
        "status": result['status'],
        "phone_number": transaction.phone_number,
        "amount": transaction.amount,
        "expiry": transaction.expiry.isoformat() if transaction.expiry else None
    }), 200

@payments_bp.route('/history', methods=['GET'])
@jwt_required()
def get_payment_history():
    """Get payment history for the authenticated user."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        logger.warning(f"Payment history fetch failed: user_id={user_id}")
        return jsonify({"error": "User not found"}), 404

    transactions = Transaction.query.filter_by(phone_number=user.phone_number).all()
    history = [
        {
            "transaction_id": t.transaction_id,
            "package_id": t.package_id,
            "amount": t.amount,
            "status": t.status,
            "created_at": t.created_at.isoformat(),
            "expiry": t.expiry.isoformat() if t.expiry else None
        }
        for t in transactions
    ]

    logger.info(f"Payment history fetched: user_id={user_id}")
    return jsonify({"history": history}), 200

@payments_bp.route("/momo/callback", methods=["POST"])
def momo_callback():
    data = request.get_json()
    print(f"Callback received: {data}")
    return jsonify({
        "status": "received",
        "transaction_id": data.get("transaction_id"),
        "status": data.get("status"),
        "amount": data.get("amount"),
        "phone_number": data.get("phone_number"),
        "package_id": data.get("package_id"),
        "expiry": data.get("expiry")
    }), 200
    
@payments_bp.route('/generate-codes', methods=['POST'])
@jwt_required()
def generate_access_codes():
    """Admin-only endpoint to generate unique access codes for a plan."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        logger.warning(f"Unauthorized attempt to generate codes: user_id={user_id}")
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    if not data or not data.get('plan_id') or not data.get('quantity'):
        logger.warning("Generate codes failed: Missing plan_id or quantity")
        return jsonify({"error": "Plan ID and quantity are required"}), 400

    plan_id = data.get('plan_id')
    quantity = data.get('quantity')

    package = next((p for p in PACKAGES if p['id'] == plan_id), None)
    if not package:
        logger.warning(f"Generate codes failed: Invalid plan ID: {plan_id}")
        return jsonify({"error": "Invalid plan ID"}), 404

    if not isinstance(quantity, int) or quantity <= 0 or quantity > 100:
        logger.warning(f"Generate codes failed: Invalid quantity: {quantity}")
        return jsonify({"error": "Quantity must be an integer between 1 and 100"}), 400

    codes = []
    try:
        for _ in range(quantity):
            max_attempts = 10
            for _ in range(max_attempts):
                code = generate_random_code()
                if not AccessCode.query.filter_by(code=code).first():
                    access_code = AccessCode(
                        code=code,
                        plan_id=plan_id,
                        duration_hours=package['duration_hours'],
                        price=package['price'],
                        status='unused'
                    )
                    db.session.add(access_code)
                    codes.append({
                        "code": code,
                        "plan_name": package['name'],
                        "duration_hours": package['duration_hours'],
                        "price": package['price']
                    })
                    break
            else:
                logger.error(f"Failed to generate unique code after {max_attempts} attempts")
                return jsonify({"error": "Unable to generate unique code. Try again."}), 500

        db.session.commit()
        # Calculate remaining codes
        max_codes = 36**6  # 6 characters (A-Z, 0-9)
        used_codes = AccessCode.query.count()
        remaining_codes = max_codes - used_codes

        logger.info(f"Generated {quantity} access codes for plan_id={plan_id} by user_id={user_id}")
        return jsonify({
            "message": f"Generated {quantity} access codes",
            "codes": codes,
            "remaining_codes": remaining_codes
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to generate codes: {str(e)}")
        return jsonify({"error": "Server error", "details": str(e)}), 500
    
# @payments_bp.route('/generate-codes', methods=['POST'])
# @jwt_required()
# def generate_access_codes():
#     """Admin-only endpoint to generate a specified number of access codes for a plan."""
#     user_id = get_jwt_identity()
#     user = User.query.get(user_id)
#     if not user or not user.is_admin:
#         logger.warning(f"Unauthorized attempt to generate codes: user_id={user_id}")
#         return jsonify({"error": "Admin access required"}), 403

#     data = request.get_json()
#     if not data or not data.get('plan_id') or not data.get('quantity'):
#         logger.warning("Generate codes failed: Missing plan_id or quantity")
#         return jsonify({"error": "Plan ID and quantity are required"}), 400

#     plan_id = data.get('plan_id')
#     quantity = data.get('quantity')

#     # Validate plan
#     package = next((p for p in PACKAGES if p['id'] == plan_id), None)
#     if not package:
#         logger.warning(f"Generate codes failed: Invalid plan ID: {plan_id}")
#         return jsonify({"error": "Invalid plan ID"}), 404

#     # Validate quantity
#     if not isinstance(quantity, int) or quantity <= 0 or quantity > 100:
#         logger.warning(f"Generate codes failed: Invalid quantity: {quantity}")
#         return jsonify({"error": "Quantity must be an integer between 1 and 100"}), 400

#     # Generate codes
#     codes = []
#     for _ in range(quantity):
#         # Ensure code is unique
#         while True:
#             code = generate_random_code()
#             if not AccessCode.query.filter_by(code=code).first():
#                 break

#         access_code = AccessCode(
#             code=code,
#             plan_id=plan_id,
#             duration_hours=package['duration_hours'],
#             price=package['price'],
#             status='unused'
#         )
#         db.session.add(access_code)
#         codes.append({
#             "code": code,
#             "plan_name": package['name'],
#             "duration_hours": package['duration_hours'],
#             "price": package['price']
#         })

#     db.session.commit()
#     logger.info(f"Generated {quantity} access codes for plan_id={plan_id} by user_id={user_id}")
#     return jsonify({"message": f"Generated {quantity} access codes", "codes": codes}), 200

@payments_bp.route('/activate-code', methods=['POST'])
def activate_access_code():
    """Activate an access code, store MAC address, and start session."""
    data = request.get_json()
    if not data or not data.get('code'):
        logger.warning("Activate code failed: Missing code")
        return jsonify({"error": "Access code is required"}), 400

    code = data.get('code')
    mac_address = request.headers.get('X-Client-MAC') or data.get('mac_address')
    if not mac_address:
        logger.warning(f"Activate code failed: Missing MAC address for code={code}")
        return jsonify({"error": "Device MAC address is required"}), 400

    access_code = AccessCode.query.filter_by(code=code).first()
    if not access_code:
        logger.warning(f"Activate code failed: Invalid code: {code}")
        return jsonify({"error": "Invalid access code"}), 404

    if access_code.status != 'unused':
        logger.warning(f"Activate code failed: Code already used: {code}, status={access_code.status}")
        return jsonify({"error": "Access code has already been used or expired"}), 400

    try:
        access_code.status = 'used'
        access_code.mac_address = mac_address
        access_code.used_at = datetime.utcnow()
        access_code.activated_at = datetime.utcnow()
        access_code.expiry = datetime.utcnow() + timedelta(hours=access_code.duration_hours)
        db.session.commit()
        logger.info(f"Access code activated: code={code}, mac_address={mac_address}")
        return jsonify({
            "message": "Access code activated successfully. Session started.",
            "code": code,
            "plan_id": access_code.plan_id,
            "duration_hours": access_code.duration_hours,
            "price": access_code.price,
            "expiry": access_code.expiry.isoformat()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to activate code: {code}, error={str(e)}")
        return jsonify({"error": "Server error", "details": str(e)}), 500

@payments_bp.route('/start-session', methods=['POST'])
def start_session():
    """Start the countdown for an access code when the user connects to the internet."""
    data = request.get_json()
    if not data or not data.get('code'):
        logger.warning("Start session failed: Missing code")
        return jsonify({"error": "Access code is required"}), 400

    code = data.get('code')
    access_code = AccessCode.query.filter_by(code=code).first()
    if not access_code:
        logger.warning(f"Start session failed: Invalid code: {code}")
        return jsonify({"error": "Invalid access code"}), 404

    if access_code.status != 'pending':
        logger.warning(f"Start session failed: Code not pending: {code}, status={access_code.status}")
        return jsonify({"error": "Access code is not pending activation"}), 400

    # Start the countdown
    access_code.status = 'activated'
    access_code.expiry = datetime.utcnow() + timedelta(hours=access_code.duration_hours)
    db.session.commit()

    logger.info(f"Session started for access code: code={code}, expiry={access_code.expiry}")
    return jsonify({
        "message": "Session started",
        "code": code,
        "plan_id": access_code.plan_id,
        "duration_hours": access_code.duration_hours,
        "price": access_code.price,
        "expiry": access_code.expiry.isoformat()
    }), 200
# @payments_bp.route('/check-code-access', methods=['GET'])
# def check_code_access():
#     """Check if an access code is still valid and provides access."""
#     code = request.args.get('code')
#     if not code:
#         return jsonify({"error": "Access code required"}), 400

#     access_code = AccessCode.query.filter_by(code=code).first()
#     if not access_code:
#         logger.warning(f"Check code access failed: Invalid code: {code}")
#         return jsonify({"error": "Invalid access code"}), 404

#     if access_code.status != 'activated':
#         logger.warning(f"Check code access failed: Code not activated: {code}")
#         return jsonify({"error": "Access code not activated"}), 400

#     current_time = datetime.utcnow()
#     if access_code.expiry < current_time:
#         access_code.status = 'expired'
#         db.session.commit()
#         logger.info(f"Access code expired: code={code}")
#         return jsonify({"error": "Access code has expired"}), 400

#     return jsonify({
#         "message": "Access granted",
#         "code": code,
#         "remaining_time": (access_code.expiry - current_time).total_seconds() / 3600  # Remaining hours
#     }), 200
    
@payments_bp.route('/check-code-access', methods=['GET'])
def check_code_access():
    """Check if an access code is still valid and provides access."""
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Access code required"}), 400

    access_code = AccessCode.query.filter_by(code=code).first()
    if not access_code:
        logger.warning(f"Check code access failed: Invalid code: {code}")
        return jsonify({"error": "Invalid access code"}), 404

    if access_code.status == 'unused':
        logger.warning(f"Check code access failed: Code not activated: {code}")
        return jsonify({"error": "Access code not yet activated"}), 400

    if access_code.status == 'pending':
        logger.info(f"Check code access: Code pending: {code}")
        return jsonify({
            "message": "Access code pending. Connect to the internet to start your session.",
            "code": code
        }), 200

    if access_code.status != 'activated':
        logger.warning(f"Check code access failed: Code not activated: {code}")
        return jsonify({"error": "Access code not activated"}), 400

    current_time = datetime.utcnow()
    if access_code.expiry < current_time:
        access_code.status = 'expired'
        db.session.commit()
        logger.info(f"Access code expired: code={code}")
        return jsonify({"error": "Access code has expired"}), 400

    return jsonify({
        "message": "Access granted",
        "code": code,
        "remaining_time": (access_code.expiry - current_time).total_seconds() / 3600
    }), 200