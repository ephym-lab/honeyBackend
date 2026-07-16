"""
Diagnostic script to test SendGrid configuration and identify issues
"""

from app.services.email_service import EmailService
import os
from dotenv import load_dotenv

load_dotenv()

def test_sendgrid_config():
    print("=" * 60)
    print("SendGrid Configuration Diagnostic")
    print("=" * 60)
    print()
    
    # Check environment variables
    print("1️⃣ Checking environment variables...")
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("EMAIL_FROM")
    from_name = os.getenv("EMAIL_FROM_NAME")
    
    if not api_key:
        print("   ❌ SENDGRID_API_KEY not found in .env")
        return
    else:
        print(f"   ✅ SENDGRID_API_KEY found: {api_key[:10]}...")
    
    if not from_email:
        print("   ❌ EMAIL_FROM not found in .env")
        return
    else:
        print(f"   ✅ EMAIL_FROM: {from_email}")
    
    print(f"   ✅ EMAIL_FROM_NAME: {from_name}")
    print()
    
    # Try to initialize EmailService
    print("2️⃣ Initializing EmailService...")
    try:
        email_service = EmailService()
        print("   ✅ EmailService initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize EmailService: {str(e)}")
        return
    print()
    
    # Get test email from user
    test_email = input("3️⃣ Enter your email address to receive a test email: ").strip()
    
    if not test_email or '@' not in test_email:
        print("   ❌ Invalid email address")
        return
    
    # Send test email
    print(f"\n4️⃣ Sending test email to {test_email}...")
    
    html_body = """
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1 style="color: #8B4513;">🕯️ SendGrid Test Email</h1>
            <p>This is a test email from your Luxe Candles backend.</p>
            <p>If you're seeing this, SendGrid is working correctly!</p>
        </body>
    </html>
    """
    
    try:
        success = email_service.send_html_email(
            to_email=test_email,
            subject="SendGrid Test Email - Luxe Candles",
            html_body=html_body
        )
        
        if success:
            print("   ✅ Email sent successfully!")
            print()
            print("📬 Check your inbox (and spam folder)")
            print("💡 If you don't receive it, check:")
            print("   1. SendGrid dashboard for delivery status")
            print("   2. Verify your sender email in SendGrid")
            print("   3. Check API key permissions")
        else:
            print("   ❌ Email sending failed")
            print()
            print("💡 Common issues:")
            print("   1. Sender email not verified in SendGrid")
            print("   2. Invalid or expired API key")
            print("   3. SendGrid account not fully set up")
            print("   4. Free tier daily limit exceeded (100 emails/day)")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        print()
        print("💡 This error suggests:")
        if "401" in str(e) or "Unauthorized" in str(e):
            print("   - Invalid API key")
        elif "403" in str(e) or "Forbidden" in str(e):
            print("   - Sender email not verified")
            print("   - API key doesn't have send permissions")
        else:
            print(f"   - {str(e)}")
    
    print()
    print("=" * 60)
    print("Diagnostic complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_sendgrid_config()
