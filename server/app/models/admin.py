from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
import logging

logger = logging.getLogger(__name__)

class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)
    is_superuser = db.Column(db.Boolean, default=False)
    otp_secret = db.Column(db.String(32), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=16
        )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_otp_secret(self):
        """Generate a new TOTP secret if none exists."""
        if not self.otp_secret:
            self.otp_secret = pyotp.random_base32()
            return self.otp_secret
        return self.otp_secret

    def get_totp_uri(self):
        """Generate a TOTP URI for QR code generation."""
        return pyotp.totp.TOTP(self.otp_secret).provisioning_uri(
            name=self.username,
            issuer_name='InternetPortal'
        )

    def verify_totp(self, token):
        """Verify a TOTP token."""
        logger.debug(f"Inside verify_totp: token={token}, otp_secret={self.otp_secret}")
        totp = pyotp.TOTP(self.otp_secret)
        result = totp.verify(token, valid_window=1)
        logger.debug(f"TOTP verification result: {result}")
        return result

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username
        }
        