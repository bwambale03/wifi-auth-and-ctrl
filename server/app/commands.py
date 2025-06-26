# app/commands.py
import click
from flask.cli import with_appcontext
from flask import current_app
from app.extensions import db
from app.models.user import User
from app.models.admin import Admin
import os
from dotenv import load_dotenv
import pyotp
import qrcode

# Load environment variables
load_dotenv()

def display_qr_code(uri):
    """Display QR code in terminal or provide instructions."""
    try:
        qr = qrcode.QRCode()
        qr.add_data(uri)
        qr.print_ascii(tty=True)
    except Exception as e:
        click.echo(f"⚠️ Couldn't display QR code: {str(e)}")
        click.echo("📱 Manually enter this TOTP secret into your authenticator app:")
        click.echo(f"Secret: {uri.split('secret=')[1].split('&')[0]}")
        click.echo(f"Or visit: https://qrcode.tec-it.com and paste this URL:\n{uri}")

def init_commands(app):
    """Register custom CLI commands with the Flask app."""

    @app.cli.command("reset-db")
    @with_appcontext
    def reset_db():
        """Reset database while preserving essential data."""
        try:
            click.confirm('This will DROP ALL TABLES. Continue?', abort=True)
            
            # Store critical config values
            admin_phone = os.getenv('ADMIN_PHONE_NUMBER', '+256786673468')
            admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
            admin_username = os.getenv('ADMIN_USERNAME', 'superadmin')
            admin_pass = os.getenv('ADMIN_PASSWORD', 'SecureRandomPassword2025!')
            
            # Drop all tables
            db.drop_all()
            click.echo("🗑️ Dropped all database tables")
            
            # Recreate tables
            db.create_all()
            click.echo("🔄 Recreated database schema")
            
            # Re-seed essential data
            seed_db_functional(admin_phone, admin_email, admin_username, admin_pass)
            click.echo("🌱 Reseeded essential data")
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database reset failed: {str(e)}")
            click.echo(f"❌ Error resetting database: {str(e)}", err=True)

    def seed_db_functional(admin_phone, admin_email, admin_username, admin_pass):
        """Core seeding functionality reused across commands."""
        # Create/update user in users table
        user = User.query.filter_by(phone_number=admin_phone).first()
        if not user:
            user = User(
                phone_number=admin_phone,
                email=admin_email,
                is_admin=True,
                is_superuser=True,
                is_phone_verified=True
            )
            user.set_password(admin_pass)
            db.session.add(user)
        else:
            user.email = admin_email
            user.set_password(admin_pass)
            user.is_admin = True
            user.is_superuser = True
            user.is_phone_verified = True
        db.session.commit()

        # Create/update admin in admins table
        admin = Admin.query.filter_by(username=admin_username).first()
        if not admin:
            admin = Admin(
                username=admin_username,
                is_admin=True,
                is_superuser=True
            )
            admin.set_password(admin_pass)
            admin.generate_otp_secret()
            db.session.add(admin)
        else:
            admin.set_password(admin_pass)
            if not admin.otp_secret:
                admin.generate_otp_secret()
        db.session.commit()

        # Display TOTP URI and QR code
        totp_uri = admin.get_totp_uri()
        click.echo(f"Admin TOTP URI (scan with Google Authenticator): {totp_uri}")
        display_qr_code(totp_uri)

    @app.cli.command("create-admin")
    @click.option('--username', default=os.getenv('ADMIN_USERNAME', 'superadmin'), help='Admin username')
    @click.option('--password', default=os.getenv('ADMIN_PASSWORD', 'SecureRandomPassword2025!'), help='Admin password')
    @click.option('--phone_number', default=os.getenv('ADMIN_PHONE_NUMBER', '+256786673468'), help='Admin phone number')
    @click.option('--email', default=os.getenv('ADMIN_EMAIL', 'admin@example.com'), help='Admin email')
    @with_appcontext
    def create_admin(username, password, phone_number, email):
        """Create or update an admin user in both users and admins tables."""
        try:
            # Update or create user in users table
            user = User.query.filter_by(phone_number=phone_number).first()
            if user:
                user.email = email
                user.set_password(password)
                user.is_admin = True
                user.is_phone_verified = True
                db.session.commit()
                click.echo(f"Updated user: {phone_number}")
            else:
                user = User(
                    phone_number=phone_number,
                    email=email,
                    is_admin=True,
                    is_superuser=True,
                    is_phone_verified=True
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                click.echo(f"Created user: {phone_number}")

            # Update or create admin in admins table
            admin = Admin.query.filter_by(username=username).first()
            if admin:
                admin.set_password(password)
                admin.is_superuser = True
                if not admin.otp_secret:
                    admin.generate_otp_secret()
                db.session.commit()
                click.echo(f"Updated admin: {username}")
            else:
                admin = Admin(
                    username=username,
                    is_admin=True,
                    is_superuser=True
                )
                admin.set_password(password)
                admin.generate_otp_secret()
                db.session.add(admin)
                db.session.commit()
                click.echo(f"Created admin: {username}")

            # Display TOTP URI and QR code
            totp_uri = admin.get_totp_uri()
            click.echo(f"TOTP URI (scan with Google Authenticator): {totp_uri}")
            display_qr_code(totp_uri)
        except Exception as e:
            db.session.rollback()
            click.echo(f"Error creating admin: {str(e)}", err=True)
            if 'otp_secret' in str(e):
                click.echo("⚠️ Make sure you've run migrations to add the otp_secret column")
                click.echo("Run: flask db upgrade")

    @app.cli.command("init-db")
    @with_appcontext
    def init_db():
        """Initialize the database (create tables)."""
        try:
            db.create_all()
            click.echo("✅ Database tables created")
        except Exception as e:
            click.echo(f"❌ Error initializing database: {str(e)}", err=True)

    @app.cli.command("seed-db")
    @with_appcontext
    def seed_db():
        """Seed the database with initial data."""
        try:
            seed_db_functional(
                admin_phone=os.getenv('ADMIN_PHONE_NUMBER', '+256786673468'),
                admin_email=os.getenv('ADMIN_EMAIL', 'admin@example.com'),
                admin_username=os.getenv('ADMIN_USERNAME', 'superadmin'),
                admin_pass=os.getenv('ADMIN_PASSWORD', 'SecureRandomPassword2025!')
            )
            click.echo("✅ Database seeded successfully")
        except Exception as e:
            db.session.rollback()
            click.echo(f"❌ Error seeding database: {str(e)}", err=True)
            