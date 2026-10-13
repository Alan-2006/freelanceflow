from typing import Any, Dict

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from .base import NotificationChannel


class EmailNotificationChannel(NotificationChannel):

    def send(self, recipient: str, subject: str, body: str, context: Dict[str, Any]) -> bool:
        site_url = context.get('site_url', 'http://127.0.0.1:8000')
        token = context.get('tracking_token', '')

        # HTML body with injected tracking pixel
        tracking_pixel = f'<img src="{site_url}/reminders/track/open/{token}/" width="1" height="1" style="display:none;" alt="" />'

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #334155; margin: 0; padding: 20px; }}
                .container {{ max-width: 580px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 28px; }}
                .btn {{ display: inline-block; padding: 12px 24px; background-color: #4f46e5; color: #ffffff !important; text-decoration: none; border-radius: 8px; font-weight: 600; margin-top: 16px; }}
                .footer {{ margin-top: 24px; font-size: 11px; color: #94a3b8; border-top: 1px solid #f1f5f9; padding-top: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div style="white-space: pre-wrap;">{body}</div>
                {tracking_pixel}
                <div class="footer">
                    Sent via FreelanceFlow automated payment notification system.
                </div>
            </div>
        </body>
        </html>
        """

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'FreelanceFlow <no-reply@freelanceflow.local>')
        msg = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[recipient]
        )
        msg.attach_alternative(html_content, "text/html")
        return msg.send(fail_silently=False) > 0
