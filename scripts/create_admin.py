import os
import sys

# Add project root to path so we can import 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db, User
from werkzeug.security import generate_password_hash

def create_admin():
    app = create_app()
    with app.app_context():
        # Check if admin already exists
        admin_email = "admin@bugtracker.ai"
        if User.query.filter_by(email=admin_email).first():
            print(f"Admin {admin_email} already exists.")
            return

        password = "admin_password_123" # In a real app, this should be secure/env based
        new_admin = User(
            name="System Administrator",
            email=admin_email,
            role="admin",
            is_verified=True
        )
        new_admin.set_password(password)
        
        db.session.add(new_admin)
        db.session.commit()
        
        print("-" * 30)
        print("ADMIN ACCOUNT CREATED")
        print(f"Email: {admin_email}")
        print(f"Password: {password}")
        print("-" * 30)

if __name__ == "__main__":
    create_admin()
