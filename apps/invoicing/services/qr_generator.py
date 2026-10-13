import base64
import io

import qrcode


class QRGeneratorService:

    @staticmethod
    def generate_invoice_qr_base64(invoice, base_url: str = 'http://127.0.0.1:8000') -> str:
        """
        Generate base64 encoded PNG QR code.
        If freelancer has a UPI ID and currency is INR, generate a direct UPI payment QR.
        Otherwise generate a QR code pointing to the public invoice payment portal.
        """
        freelancer = invoice.freelancer
        if freelancer.upi_id and invoice.currency == 'INR':
            # UPI URI format
            data = (
                f"upi://pay?pa={freelancer.upi_id}"
                f"&pn={freelancer.display_name}"
                f"&am={invoice.balance_due}"
                f"&cu=INR"
                f"&tn={invoice.invoice_number}"
            )
        else:
            # Public invoice checkout URL
            data = f"{base_url}/invoicing/public/{invoice.public_token}/"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        encoded = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{encoded}"
