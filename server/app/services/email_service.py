# 邮件服务模块 - 处理 SMTP 邮件发送功能
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import uuid

from app.config import settings
from app.utils import get_logger


logger = get_logger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self):
        self.smtp_configured = settings.smtp_configured
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.smtp_use_tls = settings.smtp_use_tls
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Send email via SMTP.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            from_email: Sender email address (defaults to SMTP username)
            
        Returns:
            Tuple of (success, message_id)
        """
        if not self.smtp_configured:
            logger.warning("SMTP not configured, stubbing email send", to=to, subject=subject)
            return True, f"stub-{uuid.uuid4().hex[:8]}"
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email or self.smtp_username
            msg['To'] = to
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                
                server.login(self.smtp_username, self.smtp_password)
                
                # Send email
                text = msg.as_string()
                server.sendmail(msg['From'], msg['To'], text)
                
                # Generate message ID
                message_id = f"smtp-{uuid.uuid4().hex[:8]}"
                
                logger.info(
                    "Email sent successfully",
                    to=to,
                    subject=subject,
                    message_id=message_id
                )
                
                return True, message_id
        
        except Exception as e:
            logger.error(
                "Failed to send email",
                to=to,
                subject=subject,
                error=str(e)
            )
            return False, None
    
    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return self.smtp_configured


# Global email service instance
email_service = EmailService()
