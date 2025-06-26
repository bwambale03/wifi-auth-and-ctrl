from app.extensions import db
from sqlalchemy.sql import func
import logging

# Set up logging
logger = logging.getLogger(__name__)

class Transaction(db.Model):
    """Transaction model for payment records."""
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), nullable=False, index=True)
    package_id = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(db.String(36), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='PENDING')  # PENDING, SUCCESS, FAILED, REFUNDED
    expiry = db.Column(db.DateTime, nullable=True)  # Package expiry time
    created_at = db.Column(db.DateTime, server_default=func.now())
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'package_id': self.package_id,
            'amount': self.amount,
            'transaction_id': self.transaction_id,
            'status': self.status,
            'expiry': self.expiry.isoformat() if self.expiry else None,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    def __repr__(self):
        return f'<Transaction id={self.transaction_id} status={self.status}>'
    