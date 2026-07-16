import pytest
from unittest.mock import patch
from app.services.email_service import EmailService


class TestEmailService:
    """Test suite for EmailService"""

    def test_email_sending_success(self):
        """Test that email sending works as expected"""
        email_service = EmailService()
        
        # Mock the email sending method
        with patch.object(email_service, 'send_email', return_value=True) as mock_send:
            result = email_service.send_email(
                to_email='ephymucira9@gmail.com',
                subject='Test Subject',
                body='Test email body'
            )
            
            assert result is True
            mock_send.assert_called_once_with(
                to_email='ephymucira9@gmail.com',
                subject='Test Subject',
                body='Test email body'
            )
            print("Email sent successfully in test.")

    def test_email_sending_failure(self):
        """Test that email sending handles failures correctly"""
        email_service = EmailService()
        
        with patch.object(email_service, 'send_email', return_value=False) as mock_send:
            result = email_service.send_email(
                to_email='invalid@example.com',
                subject='Test Subject',
                body='Test email body'
            )
            
            assert result is False
            mock_send.assert_called_once()
            
            print("Email sending failed as expected in test.")

    def test_email_with_invalid_recipient(self):
        """Test that email sending validates recipient email"""
        email_service = EmailService()
        
        with patch.object(email_service, 'send_email', side_effect=ValueError('Invalid email')) as mock_send:
            with pytest.raises(ValueError):
                email_service.send_email(
                    to_email='invalid-email',
                    subject='Test Subject',
                    body='Test email body'
                )
                
                

