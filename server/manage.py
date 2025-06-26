from flask_migrate import MigrateCommand
from flask_migrate import MigrateCommand
from app import create_app, db
from flask_script import Manager
app = create_app()
manager = Manager(app)
app = create_app()

@app.cli.command("db")
def db_command():
    """Run database migration commands."""
    MigrateCommand.run()

if __name__ == '__main__':
    manager.run()
    