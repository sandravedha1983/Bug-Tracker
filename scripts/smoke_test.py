import os
import sys

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_app_factory():
    print("Testing app factory initialization...")
    
    # Mock environment variables for testing
    os.environ['SECRET_KEY'] = 'test-secret'
    os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost:5432/db' # Mock URL
    os.environ['MAIL_USERNAME'] = 'test@gmail.com'
    os.environ['MAIL_PASSWORD'] = 'test-pass'
    
    try:
        from app import create_app
        app = create_app()
        print("Successfully created Flask app.")
        
        # Check if routes are registered
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        if '/login' in routes:
            print("Login route is registered.")
        else:
            print("ERROR: Login route is NOT registered.")
            
        if '/init-db' in routes:
            print("Init DB route is registered.")
            
        # Check config
        if app.config['SESSION_COOKIE_SECURE'] is True:
            print("Session cookie security is enabled.")
        else:
            print("ERROR: Session cookie security is NOT enabled.")
            
        return True
    except Exception as e:
        print(f"FAILED to initialize app: {e}")
        return False

if __name__ == "__main__":
    success = test_app_factory()
    if not success:
        sys.exit(1)
    print("Smoke test passed!")
