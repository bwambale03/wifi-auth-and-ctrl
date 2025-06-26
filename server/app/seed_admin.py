import sys
import qrcode
from os.path import dirname, join
sys.path.insert(0, join(dirname(__file__), '..'))  # Add parent directory to path

from app import create_app
from app.extensions import db
from app.models.admin import Admin
from dotenv import load_dotenv
import os
import pyotp

# Load environment variables
load_dotenv()

def display_qr_code(uri):
    """Display QR code in terminal or provide instructions"""
    try:
        qr = qrcode.QRCode()
        qr.add_data(uri)
        qr.print_ascii(tty=True)
    except Exception as e:
        print(f"⚠️ Couldn't display QR code: {str(e)}")
        print("📱 Manually enter this TOTP secret into your authenticator app:")
        print(f"Secret: {uri.split('secret=')[1].split('&')[0]}")
        print(f"Or visit: https://qrcode.tec-it.com and paste this URL:\n{uri}")

app = create_app()
with app.app_context():
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD')

    if not admin_password:
        print("❌ ADMIN_PASSWORD not set in .env file. Please set it and try again.")
        sys.exit(1)

    try:
        admin = Admin.query.filter_by(username=admin_username).first()
        if admin:
            print(f"ℹ️ Admin '{admin_username}' already exists")
            if not admin.otp_secret:
                admin.generate_otp_secret()
                db.session.commit()
                print("🔒 New OTP secret generated for existing admin")
                display_qr_code(admin.get_totp_uri())
        else:
            admin = Admin(username=admin_username)
            admin.set_password(admin_password)
            admin.generate_otp_secret()
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Admin user '{admin_username}' created successfully")
            display_qr_code(admin.get_totp_uri())
            
    except Exception as e:
        print(f"❌ Error creating admin: {str(e)}")
        if 'otp_secret' in str(e):
            print("⚠️ Make sure you've run migrations to add the otp_secret column")
            print("Run: flask db upgrade")
        sys.exit(1)
        