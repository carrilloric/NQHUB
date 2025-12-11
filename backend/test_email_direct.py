"""Test email sending directly with detailed error output"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

# Get settings from .env
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")

print(f"📧 Testing email configuration:")
print(f"   Host: {SMTP_HOST}")
print(f"   Port: {SMTP_PORT}")
print(f"   User: {SMTP_USER}")
print(f"   From: {FROM_EMAIL}")
print()

try:
    # Create test message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'NQHUB Test Email'
    msg['From'] = FROM_EMAIL
    msg['To'] = 'ricardocarrillo3@gmail.com'
    
    text_part = MIMEText("This is a test email from NQHUB", 'plain')
    msg.attach(text_part)
    
    print("🔌 Connecting to SMTP server...")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        server.set_debuglevel(2)  # Enable verbose output
        
        print("\n🔒 Starting TLS...")
        server.starttls()
        
        print(f"\n🔑 Logging in as {SMTP_USER}...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        
        print("\n📤 Sending email...")
        server.send_message(msg)
        
    print("\n✅ Email sent successfully!")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ Authentication failed: {e}")
    print("Check your Gmail App Password is correct")
    
except smtplib.SMTPException as e:
    print(f"\n❌ SMTP Error: {e}")
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
