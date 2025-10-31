"""
Email Service
Handles sending emails via SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


def create_password_reset_email_html(reset_link: str, user_email: str) -> str:
    """Create HTML email template for password reset"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .container {{
                background-color: #f9f9f9;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: bold;
                color: #FFB800;
            }}
            .content {{
                background-color: white;
                padding: 30px;
                border-radius: 8px;
            }}
            .button {{
                display: inline-block;
                background-color: #00D9FF;
                color: #0A192F !important;
                padding: 14px 30px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                font-size: 12px;
                color: #777;
            }}
            .warning {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 12px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">NQHUB</div>
                <p style="color: #666;">Professional Trading Platform</p>
            </div>

            <div class="content">
                <h2>Password Reset Request</h2>
                <p>Hello,</p>
                <p>We received a request to reset the password for your NQHUB account (<strong>{user_email}</strong>).</p>

                <p>Click the button below to reset your password:</p>

                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </div>

                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #666; font-size: 13px;">{reset_link}</p>

                <div class="warning">
                    <strong>⚠️ Security Notice:</strong><br>
                    This link will expire in 7 days. If you didn't request this password reset, please ignore this email.
                </div>
            </div>

            <div class="footer">
                <p>© 2024 NQHUB. All rights reserved.</p>
                <p>This is an automated message, please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """


def create_password_reset_email_text(reset_link: str, user_email: str) -> str:
    """Create plain text email template for password reset"""
    return f"""
    NQHUB - Password Reset Request

    Hello,

    We received a request to reset the password for your NQHUB account ({user_email}).

    Click the link below to reset your password:
    {reset_link}

    This link will expire in 7 days.

    If you didn't request this password reset, please ignore this email.

    ---
    © 2024 NQHUB. All rights reserved.
    This is an automated message, please do not reply to this email.
    """


async def send_password_reset_email(
    email: str,
    token: str,
    frontend_url: Optional[str] = None
) -> bool:
    """
    Send password reset email to user

    Args:
        email: User's email address
        token: Password reset token
        frontend_url: Frontend base URL (defaults to settings.FRONTEND_URL)

    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        # Use provided frontend_url or fall back to settings
        base_url = frontend_url or getattr(settings, 'FRONTEND_URL', 'http://localhost:3001')
        reset_link = f"{base_url}/reset-password?token={token}"

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'NQHUB - Password Reset Request'
        msg['From'] = settings.FROM_EMAIL
        msg['To'] = email

        # Create both plain text and HTML versions
        text_part = MIMEText(create_password_reset_email_text(reset_link, email), 'plain')
        html_part = MIMEText(create_password_reset_email_html(reset_link, email), 'html')

        msg.attach(text_part)
        msg.attach(html_part)

        # Connect to SMTP server and send
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            # Use STARTTLS if not using port 1025 (Mailpit)
            if settings.SMTP_PORT != 1025:
                server.starttls()

            # Login if credentials provided
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

            server.send_message(msg)

        logger.info(f"Password reset email sent successfully to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {str(e)}")
        return False


async def send_invitation_email(
    email: str,
    token: str,
    role: str,
    frontend_url: Optional[str] = None
) -> bool:
    """
    Send invitation email to new user (future enhancement)

    Args:
        email: User's email address
        token: Invitation token
        role: User role
        frontend_url: Frontend base URL

    Returns:
        True if email was sent successfully, False otherwise
    """
    # TODO: Implement invitation email template similar to password reset
    # This can be implemented when automatic invitation emails are needed
    logger.warning("Invitation email sending not yet implemented")
    return False
