"""
Test script for SendGrid email service
Run this to verify your SendGrid integration is working correctly
"""

from app.services.email_service import EmailService
import sys

def test_email_service():
    print("🧪 Testing SendGrid Email Service...\n")
    
    try:
        # Initialize the service
        print("1️⃣ Initializing EmailService...")
        email_service = EmailService()
        print("   ✅ EmailService initialized successfully\n")
        
        # Get recipient email
        recipient = input("📧 Enter your email address to receive a test email: ").strip()
        
        if not recipient or '@' not in recipient:
            print("❌ Invalid email address")
            return False
        
        # Send plain text email
        print(f"\n2️⃣ Sending plain text test email to {recipient}...")
        success_plain = email_service.send_email(
            to_email=recipient,
            subject="Test Email from Luxe Candles (Plain Text)",
            body="Hello! This is a plain text test email from your Luxe Candles backend using SendGrid.",
            is_html=False
        )
        
        if success_plain:
            print("   ✅ Plain text email sent successfully\n")
        else:
            print("   ❌ Failed to send plain text email\n")
            return False
        
        # Send HTML email
        print(f"3️⃣ Sending HTML test email to {recipient}...")
        html_body = """
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px;">
                    <h1 style="color: #8B4513;">🕯️ Luxe Candles</h1>
                    <h2 style="color: #333;">SendGrid Integration Test</h2>
                    <p style="color: #666; line-height: 1.6;">
                        Congratulations! Your SendGrid email service is working correctly.
                    </p>
                    <p style="color: #666; line-height: 1.6;">
                        This HTML email confirms that your backend can now send beautiful, 
                        formatted emails to your customers.
                    </p>
                    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>✅ Email service is operational</strong>
                    </div>
                    <p style="color: #999; font-size: 12px; margin-top: 30px;">
                        Sent from Luxe Candles Backend
                    </p>
                </div>
            </body>
        </html>
        """
        
        success_html = email_service.send_html_email(
            to_email=recipient,
            subject="Test Email from Luxe Candles (HTML)",
            html_body=html_body
        )
        
        if success_html:
            print("   ✅ HTML email sent successfully\n")
        else:
            print("   ❌ Failed to send HTML email\n")
            return False
        
        print("=" * 60)
        print("🎉 SUCCESS! All tests passed!")
        print("=" * 60)
        print("\n📬 Check your inbox (and spam folder) for the test emails.")
        print("💡 You can also view email activity in your SendGrid dashboard:")
        print("   https://app.sendgrid.com/email_activity\n")
        
        return True
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {str(e)}")
        print("\n💡 Make sure you have set SENDGRID_API_KEY in your .env file")
        print("   See sendgrid_setup.md for instructions\n")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_email_service()
    sys.exit(0 if success else 1)
