import io

from django.template.loader import render_to_string

from .qr_generator import QRGeneratorService


class InvoicePDFGenerator:

    @staticmethod
    def generate_invoice_pdf(invoice, site_url: str = 'http://127.0.0.1:8000') -> bytes:
        """
        Render invoice template and compile to PDF bytes.
        Uses WeasyPrint if available; falls back to ReportLab canvas to ensure 100% reliability.
        """
        qr_code_base64 = QRGeneratorService.generate_invoice_qr_base64(invoice, site_url)
        context = {
            'invoice': invoice,
            'freelancer': invoice.freelancer,
            'client': invoice.client,
            'line_items': invoice.line_items.all(),
            'qr_code_base64': qr_code_base64,
            'site_url': site_url,
        }

        # Attempt WeasyPrint first
        try:
            from weasyprint import HTML
            html_string = render_to_string('invoicing/pdf/invoice.html', context)
            pdf_bytes = HTML(string=html_string, base_url=site_url).write_pdf()
            return pdf_bytes
        except Exception:
            # Fallback using ReportLab
            return InvoicePDFGenerator._generate_reportlab_pdf(invoice)

    @staticmethod
    def _generate_reportlab_pdf(invoice) -> bytes:
        """Lightweight ReportLab fallback PDF generator."""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Header
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, height - 50, f"INVOICE {invoice.invoice_number}")

        p.setFont("Helvetica", 10)
        p.drawString(50, height - 75, f"Date: {invoice.issue_date} | Due Date: {invoice.due_date}")
        p.drawString(50, height - 90, f"Status: {invoice.status}")

        # Freelancer & Client info
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, height - 120, f"From: {invoice.freelancer.display_name}")
        p.drawString(320, height - 120, f"To: {invoice.client.display_title}")

        p.setFont("Helvetica", 9)
        if invoice.freelancer.tax_id:
            p.drawString(50, height - 135, f"Tax ID: {invoice.freelancer.tax_id}")
        p.drawString(320, height - 135, f"Email: {invoice.client.email}")

        # Table Header
        y = height - 175
        p.setFillColorRGB(0.9, 0.9, 0.95)
        p.rect(50, y - 5, 510, 20, fill=True, stroke=False)
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(60, y, "Description")
        p.drawString(350, y, "Qty")
        p.drawString(420, y, "Price")
        p.drawString(490, y, "Total")

        # Line items
        p.setFont("Helvetica", 9)
        y -= 20
        for item in invoice.line_items.all():
            p.drawString(60, y, str(item.description)[:45])
            p.drawString(350, y, str(item.quantity))
            p.drawString(420, y, f"${item.unit_price}")
            p.drawString(490, y, f"${item.total}")
            y -= 18

        # Totals
        y -= 20
        p.line(50, y + 10, 560, y + 10)
        p.setFont("Helvetica", 10)
        p.drawString(380, y - 10, f"Subtotal: ${invoice.subtotal}")
        if invoice.tax_amount > 0:
            p.drawString(380, y - 25, f"Tax ({invoice.tax_rate}%): ${invoice.tax_amount}")
        if invoice.late_fee_amount > 0:
            p.drawString(380, y - 40, f"Late Fee: ${invoice.late_fee_amount}")

        p.setFont("Helvetica-Bold", 12)
        p.drawString(380, y - 60, f"Total Due: ${invoice.total_amount}")

        # Payment details
        if invoice.freelancer.bank_details or invoice.freelancer.upi_id:
            p.setFont("Helvetica-Bold", 10)
            p.drawString(50, y - 40, "Payment Instructions:")
            p.setFont("Helvetica", 8)
            if invoice.freelancer.upi_id:
                p.drawString(50, y - 55, f"UPI ID: {invoice.freelancer.upi_id}")
            if invoice.freelancer.bank_details:
                p.drawString(50, y - 70, f"Bank: {invoice.freelancer.bank_details[:50]}")

        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
