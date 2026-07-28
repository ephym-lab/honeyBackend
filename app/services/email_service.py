import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

class EmailService:
    def __init__(self, host=None, port=None, username=None, password=None, from_email=None, from_name=None):
        self.host = host or os.getenv("EMAIL_HOST", "smtp.gmail.com")
        self.port = int(port or os.getenv("EMAIL_PORT", 587))
        self.username = username or os.getenv("EMAIL_USERNAME")
        self.password = password or os.getenv("EMAIL_PASSWORD")
        self.from_email = from_email or os.getenv("EMAIL_FROM", "ephymucira@gmail.com")
        self.from_name = from_name or os.getenv("EMAIL_FROM_NAME", "HoneyBiz")
        
        if not self.username or not self.password:
            print("Warning: EMAIL_USERNAME or EMAIL_PASSWORD not set. Email sending will fail.")

    def send_email(self, to_email, subject, body, is_html=False):
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            content_type = "html" if is_html else "plain"
            msg.attach(MIMEText(body, content_type))

            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                # pyrefly: ignore [bad-argument-type]
                server.login(self.username, self.password)
                server.send_message(msg)

            print(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
            
    def send_html_email(self, to_email, subject, html_body):
        return self.send_email(to_email, subject, html_body, is_html=True)
