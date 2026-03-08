from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message, Mail
from flask import url_for, render_template
import os
import logging

# Initialize mail object
mail = Mail()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_verification_token(email, secret_key):
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(email, salt='email-confirm-salt')

def confirm_verification_token(token, secret_key, expiration=3600):
    serializer = URLSafeTimedSerializer(secret_key)
    try:
        email = serializer.loads(
            token,
            salt='email-confirm-salt',
            max_age=expiration
        )
    except Exception:
        return False
    return email

def generate_verification_link(token):
    base_url = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')
    return f"{base_url}/verify-email/{token}"

def send_verification_email(to_email, token):
    """Sends a verification email to the user."""
    verify_url = generate_verification_link(token)
    
    msg = Message(
        "Verify your Bug Tracker account",
        recipients=[to_email]
    )
    
    # Text version (specific text from prompt)
    msg.body = f"""Hello,

Thank you for signing up for AI Bug Tracker.

Please verify your email by clicking the link below:

{verify_url}

This link expires in 1 hour.

If you did not create this account, please ignore this email.

Regards,
AI Bug Tracker Team"""
    
    # HTML version
    try:
        msg.html = render_template('emails/verification_email.html', verify_url=verify_url)
    except Exception as e:
        logger.warning(f"Template rendering failed, falling back to simple HTML: {e}")
        msg.html = f"""
        <p>Hello,</p>
        <p>Thank you for signing up for AI Bug Tracker.</p>
        <p>Please verify your email by clicking the link below:</p>
        <p><a href="{verify_url}">{verify_url}</a></p>
        <p>This link expires in 1 hour.</p>
        <p>If you did not create this account, please ignore this email.</p>
        <p>Regards,<br>AI Bug Tracker Team</p>
        """

    try:
        mail.send(msg)
        logger.info(f"SUCCESS: Verification email sent to {to_email}")
        return True
    except Exception as e:
        # Step 7: Improved error handling - log actual exception
        error_msg = str(e)
        logger.error(f"CRITICAL EMAIL FAILURE: Failed to send to {to_email}")
        logger.error(f"ERROR DETAILS: {error_msg}")
        
        # Check for common Gmail/SMTP errors and log them specifically
        if "Authentication failed" in error_msg or "535" in error_msg:
            logger.error("DIAGNOSIS: SMTP authentication failed. Likely incorrect MAIL_USERNAME or MAIL_PASSWORD (App Password).")
        elif "Connection refused" in error_msg:
            logger.error("DIAGNOSIS: Connection refused. Check MAIL_SERVER and MAIL_PORT.")
        
        return False

def send_resend_verification_email(to_email, token):
    """Sends a resend verification email."""
    # Reuse the same template but maybe change subject if needed
    return send_verification_email(to_email, token)
