import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from apps.invoicing.models import Invoice

logger = logging.getLogger(__name__)


class InvoiceEmailService:
    @staticmethod
    def send_invoice_email(invoice: Invoice, site_url: str) -> bool:
        """Send an invoice notification email with link to the client portal and PDF."""
        client = invoice.client
        freelancer = invoice.freelancer
        public_url = f"{site_url}/invoicing/public/{invoice.public_token}/"
        portal_url = f"{site_url}/portal/access/{client.get_or_create_portal_token()}/"

        subject = f"Invoice {invoice.invoice_number} from {freelancer.display_name} (${invoice.total_amount})"

        context = {
            'invoice': invoice,
            'client': client,
            'freelancer': freelancer,
            'public_url': public_url,
            'portal_url': portal_url,
            'site_url': site_url,
        }

        html_body = render_to_string('invoicing/email/invoice_sent.html', context)
        text_body = f"""Hello {client.name},

Please find your invoice {invoice.invoice_number} for {invoice.currency} {invoice.total_amount}.

Payment Due: {invoice.due_date.strftime('%B %d, %Y')}
View and pay online: {public_url}

Thank you for your business!
{freelancer.display_name}
"""
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'billing@freelanceflow.dev')
        recipient_list = [client.email]

        try:
            msg = EmailMultiAlternatives(subject, text_body, from_email, recipient_list)
            msg.attach_alternative(html_body, 'text/html')
            msg.send(fail_silently=False)
            logger.info("Sent invoice %s to %s", invoice.invoice_number, client.email)
            return True
        except Exception as e:
            logger.error("Failed to send invoice email %s: %s", invoice.invoice_number, e)
            return False
