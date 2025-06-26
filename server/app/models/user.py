from app.extensions import db
from sqlalchemy.sql import func
import bcrypt
import logging

# Set up logging
logger = logging.getLogger(__name__)

class User(db.Model):
    """User model for registered and anonymous users."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_superuser = db.Column(db.Boolean, default=False, nullable=False)
    is_phone_verified = db.Column(db.Boolean, default=False, nullable=False)
    otp = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    dummy_field = db.Column(db.String(50), nullable=True)  # Add this line

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        logger.debug(f"Password set for user: phone={self.phone_number}")

    def check_password(self, password):
        """Verify the user's password."""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def __repr__(self):
        return f'<User phone={self.phone_number} email={self.email}>'
    
    def to_dict(self):
        """Convert the User object to a dictionary."""
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'email': self.email,
            'is_admin': self.is_admin,
            'is_superuser': self.is_superuser,
            'is_phone_verified': self.is_phone_verified,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
