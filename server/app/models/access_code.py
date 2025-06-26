from app.extensions import db
from datetime import datetime

class AccessCode(db.Model):
    __tablename__ = 'access_codes'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), unique=True, nullable=False, index=True)  # Random 12-character code
    plan_id = db.Column(db.String(10), nullable=False)  # References a package/plan (e.g., "1", "2", "3")
    duration_hours = db.Column(db.Integer, nullable=False)  # Duration in hours (e.g., 1, 24, 168)
    price = db.Column(db.Float, nullable=False)  # Price of the plan
    status = db.Column(db.String(20), nullable=False, default='unused')  # 'unused', 'activated', 'expired'
    mac_address = db.Column(db.String(17), nullable=True)  # MAC address of the device
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)  # When the code was used
    activated_at = db.Column(db.DateTime, nullable=True)  # When the code was activated
    expiry = db.Column(db.DateTime, nullable=True)  # When the access expires after activation
