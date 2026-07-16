"""
Example script to test the admin newsletter broadcast endpoint
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/v1"
ADMIN_EMAIL = "admin@luxcandles.com"
ADMIN_PASSWORD = "admin123"

def get_admin_token():
    """Login as admin and get access token"""
    print("🔐 Logging in as admin...")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
    )
    
    if response.status_code == 200:
        response = response.json()
        token = response["data"]["token"]
        print("✅ Admin login successful\n")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        return None


def send_newsletter(token):
    """Send a newsletter to all subscribers"""
    print("📧 Sending newsletter broadcast...")
    
    # Create a beautiful HTML newsletter
    html_body = """
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f9f9f9;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #8B4513; margin: 0;">🕯️ Luxe Candles</h1>
                    <p style="color: #666; margin-top: 10px;">Illuminate Your Space</p>
                </div>
                
                <h2 style="color: #333;">New Spring Collection Now Available!</h2>
                
                <p style="color: #666; line-height: 1.6;">
                    We're excited to announce the launch of our brand new Spring Collection! 
                    Discover fresh, floral scents that will transform your home into a 
                    blooming paradise.
                </p>
                
                <div style="background-color: #f0f0f0; padding: 20px; border-radius: 5px; margin: 25px 0;">
                    <h3 style="color: #8B4513; margin-top: 0;">Featured Scents:</h3>
                    <ul style="color: #666; line-height: 1.8;">
                        <li>🌸 Cherry Blossom Dreams</li>
                        <li>🌿 Fresh Garden Mint</li>
                        <li>🌺 Tropical Hibiscus</li>
                        <li>🍋 Lemon Verbena</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://luxecandles.com/shop" 
                       style="background-color: #8B4513; color: white; padding: 15px 40px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Shop Now
                    </a>
                </div>
                
                <p style="color: #999; font-size: 12px; text-align: center; margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px;">
                    You're receiving this email because you subscribed to our newsletter.<br>
                    <a href="#" style="color: #8B4513;">Unsubscribe</a>
                </p>
            </div>
        </body>
    </html>
    """
    
    newsletter_data = {
        "subject": "🌸 New Spring Collection - Limited Time Offer!",
        "html_body": html_body
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/newsletter/admin/broadcast",
        json=newsletter_data,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Newsletter broadcast successful!\n")
        print(f"📊 Results:")
        print(f"   - Emails sent: {result['emails_sent']}")
        print(f"   - Message: {result['message']}")
        if result.get('failed_emails'):
            print(f"   - Failed emails: {', '.join(result['failed_emails'])}")
    else:
        print(f"❌ Newsletter broadcast failed: {response.text}")


def main():
    print("=" * 60)
    print("Newsletter Broadcast Test")
    print("=" * 60)
    print()
    
    # Get admin token
    token = get_admin_token()
    if not token:
        return
    
    # Send newsletter
    send_newsletter(token)
    
    print()
    print("=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
