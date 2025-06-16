import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///attendance_system.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db.init_app(app)

# Set up login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import User, Student, Faculty, Course, Attendance, AbsenceRequest
    
    # Create all tables in the database
    db.create_all()

    # Import and register routes after models are created
    from routes import register_routes
    register_routes(app)

    # Setup user loader for login_manager
    from models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

if __name__ == '__main__':
    app.run(debug=True)