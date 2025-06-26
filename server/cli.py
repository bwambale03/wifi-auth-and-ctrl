import click
from flask.cli import with_appcontext
from app import create_app, db

app = create_app()

@click.command(name='create_db')
@with_appcontext
def create_db():
    """Create the database tables"""
    db.create_all()
    print("Database tables created")

# Register commands with Flask app
app.cli.add_command(create_db)
