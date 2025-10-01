#!/usr/bin/env python3
"""
Custom email sending service for InterSpark
This allows us to send emails with our own templates and tokens
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Custom email service for sending verification emails"""

    def __init__(self):
        # Email configuration from environment variables
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@interspark.com")
        self.from_name = os.getenv("FROM_NAME", "InterSpark")

    def send_verification_email(
        self, to_email: str, verification_token: str
    ) -> Dict[str, Any]:
        """
        Send email verification email with our secure token

        Args:
            to_email: Recipient email address
            verification_token: Our secure verification token

        Returns:
            Dict with success status and info
        """
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured, skipping email send")
                return {
                    "success": False,
                    "error": "Email service not configured",
                    "fallback_needed": True,
                }

            # Create email content
            site_url = os.getenv("SITE_URL", "http://localhost:5001")
            verification_link = f"{site_url}/auth/verify?token={verification_token}"

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Verify your InterSpark account"
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Create HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Verify Your InterSpark Account</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
                
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #333; margin-bottom: 10px;">Welcome to InterSpark!</h1>
                    <p style="color: #666; font-size: 16px;">Thank you for signing up! Please verify your email address to activate your account.</p>
                </div>
                
                <div style="text-align: center; margin: 40px 0;">
                    <a href="{verification_link}" 
                       style="background-color: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; font-size: 16px;">
                        Verify Email Address
                    </a>
                </div>
                
                <div style="margin: 30px 0;">
                    <p><strong>Can't click the button?</strong> Copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 4px; border: 1px solid #dee2e6;">
                        <a href="{verification_link}" style="color: #007bff;">{verification_link}</a>
                    </p>
                </div>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <p style="margin: 0; color: #856404;"><strong>⚠️ Important Security Information:</strong></p>
                    <ul style="margin: 10px 0; padding-left: 20px; color: #856404;">
                        <li>This verification link will expire in <strong>24 hours</strong></li>
                        <li>The link can only be used <strong>once</strong></li>
                        <li>Keep this email private and secure</li>
                    </ul>
                </div>
                
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
                    <p style="color: #666; font-size: 14px; margin: 5px 0;">
                        If you didn't sign up for InterSpark, please ignore this email.
                    </p>
                    <p style="color: #999; font-size: 12px; margin: 5px 0;">
                        This email was sent from InterSpark. If you have any questions, please contact our support team.
                    </p>
                </div>
                
            </body>
            </html>
            """

            # Create plain text version
            text_content = f"""
            Welcome to InterSpark!
            
            Thank you for signing up! Please verify your email address to activate your account.
            
            Click this link to verify your email:
            {verification_link}
            
            IMPORTANT: This verification link will expire in 24 hours and can only be used once.
            
            If you didn't sign up for InterSpark, please ignore this email.
            
            ---
            InterSpark Support Team
            """

            # Attach parts
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")

            msg.attach(part1)
            msg.attach(part2)

            # Send email
            if self.smtp_port == 465:
                # Port 465 uses SSL/TLS (not STARTTLS)
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
            else:
                # Port 587 and others use STARTTLS
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)

            logger.info(f"Verification email sent successfully to {to_email}")
            return {
                "success": True,
                "message": "Verification email sent successfully",
                "verification_link": verification_link,
            }

        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            return {"success": False, "error": str(e), "fallback_needed": True}


# Global instance
email_service = EmailService()
