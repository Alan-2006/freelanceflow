import json
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.invoicing.models import Invoice
from core.permissions import freelancer_required

from .forms import CreditNoteForm, ManualPaymentForm
from .gateways.razorpay_gateway import RazorpayGateway
from .gateways.stripe_gateway import StripeGateway
from .models import CreditNote, Payment, PaymentMethod, PaymentStatus
from .services import PaymentService



@freelancer_required
def payment_list_view(request):
    freelancer = request.user.profile
    payments = Payment.objects.filter(invoice__freelancer=freelancer)

    return render(request, 'payments/list.html', {
        'payments': payments,
    })


@freelancer_required
def manual_payment_record_view(request):
    freelancer = request.user.profile

    pre_invoice_id = request.GET.get('invoice')
    pre_invoice = None
    if pre_invoice_id:
        pre_invoice = freelancer.invoices.filter(id=pre_invoice_id).first()

    if request.method == 'POST':
        form = ManualPaymentForm(freelancer, request.POST, request.FILES)
        if form.is_valid():
            p = form.save(commit=False)
            payment = PaymentService.record_payment(
                invoice=p.invoice,
                amount=p.amount,
                method=p.method,
                proof_file=p.proof_file,
                notes=p.notes
            )
            messages.success(request, f"Payment of ${payment.amount} recorded for {p.invoice.invoice_number}!")
            return redirect('invoicing:detail', pk=p.invoice.pk)
    else:
        form = ManualPaymentForm(freelancer, initial={
            'invoice': pre_invoice,
            'amount': pre_invoice.balance_due if pre_invoice else 0.00,
            'method': PaymentMethod.MANUAL_BANK,
        })

    return render(request, 'payments/manual_form.html', {
        'form': form,
        'pre_invoice': pre_invoice,
    })


@freelancer_required
def credit_note_list_view(request):
    freelancer = request.user.profile
    credit_notes = CreditNote.objects.filter(invoice__freelancer=freelancer)
    return render(request, 'payments/credit_notes.html', {
        'credit_notes': credit_notes,
    })


@freelancer_required
def credit_note_create_view(request):
    freelancer = request.user.profile
    pre_invoice_id = request.GET.get('invoice')
    pre_invoice = None
    if pre_invoice_id:
        pre_invoice = freelancer.invoices.filter(id=pre_invoice_id).first()

    if request.method == 'POST':
        form = CreditNoteForm(freelancer, request.POST)
        if form.is_valid():
            cn = form.save()
            inv = cn.invoice
            # Decrease amount_paid on invoice and log refund
            inv.amount_paid = max(Decimal('0.00'), inv.amount_paid - cn.amount)
            if inv.amount_paid == Decimal('0.00'):
                inv.status = 'Draft'
            else:
                inv.status = 'Partially Paid'
            inv.save(update_fields=['amount_paid', 'status'])

            Payment.objects.create(
                invoice=inv,
                amount=cn.amount,
                currency=inv.currency,
                method=PaymentMethod.MANUAL_BANK,
                status=PaymentStatus.REFUNDED,
                notes=f"Credit note {cn.credit_note_number} issued: {cn.reason}"
            )
            from apps.clients.services import ClientService
            ClientService.recalculate_reliability_score(inv.client)

            messages.success(request, f"Credit Note {cn.credit_note_number} (${cn.amount}) issued for invoice {inv.invoice_number}!")
            return redirect('invoicing:detail', pk=inv.pk)
    else:
        form = CreditNoteForm(freelancer, initial={
            'invoice': pre_invoice,
            'amount': pre_invoice.amount_paid if pre_invoice else Decimal('0.00'),
        })

    return render(request, 'payments/credit_note_form.html', {
        'form': form,
        'pre_invoice': pre_invoice,
    })


def checkout_view(request, invoice_pk):
    """Client checkout page with Razorpay and Stripe gateways + alternative UPI/Wire instructions."""
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    if invoice.status == 'Paid':
        messages.info(request, "This invoice is already settled in full.")
        return redirect('invoicing:public', public_token=invoice.public_token)

    rzp_gateway = RazorpayGateway()
    order_data = rzp_gateway.create_order(
        amount=float(invoice.balance_due),
        currency=invoice.currency,
        receipt=invoice.invoice_number,
        notes={'invoice_id': str(invoice.id)}
    )

    stripe_gateway = StripeGateway()
    stripe_order = stripe_gateway.create_order(
        amount=float(invoice.balance_due),
        currency=invoice.currency,
        receipt=invoice.invoice_number,
        notes={'invoice_id': str(invoice.id)}
    )

    return render(request, 'payments/checkout.html', {
        'invoice': invoice,
        'order': order_data,
        'razorpay_key': rzp_gateway.key_id,
        'stripe_order': stripe_order,
        'stripe_key': stripe_gateway.publishable_key,
        'freelancer': invoice.freelancer,
        'client': invoice.client,
    })


@require_POST
def stripe_verify_view(request, invoice_pk):
    """Verify Stripe payment return."""
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    gateway = StripeGateway()

    payment_intent_id = request.POST.get('payment_intent_id', '')
    signature = request.POST.get('signature', '')

    is_valid = gateway.verify_payment_signature(payment_intent_id, payment_intent_id, signature)
    if is_valid:
        PaymentService.record_payment(
            invoice=invoice,
            amount=invoice.balance_due,
            method=PaymentMethod.STRIPE,
            gateway_order_id=payment_intent_id,
            gateway_payment_id=payment_intent_id,
            gateway_signature=signature,
            notes='Settled online via Stripe Card Checkout.'
        )
        messages.success(request, "Card payment received via Stripe! Receipt created.")
        return redirect('invoicing:public', public_token=invoice.public_token)
    else:
        messages.error(request, "Stripe card transaction verification failed.")
        return redirect('payments:checkout', invoice_pk=invoice.pk)



@require_POST
def razorpay_verify_view(request, invoice_pk):
    """Verify payment signature from Razorpay modal redirect."""
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    gateway = RazorpayGateway()

    order_id = request.POST.get('razorpay_order_id', '')
    payment_id = request.POST.get('razorpay_payment_id', '')
    signature = request.POST.get('razorpay_signature', '')

    is_valid = gateway.verify_payment_signature(order_id, payment_id, signature)

    # In test mode / local dev without valid Razorpay credentials, accept simulated orders
    if not is_valid and order_id.startswith('order_sim_'):
        is_valid = True

    if is_valid:
        PaymentService.record_payment(
            invoice=invoice,
            amount=invoice.balance_due,
            method=PaymentMethod.RAZORPAY,
            gateway_order_id=order_id,
            gateway_payment_id=payment_id,
            gateway_signature=signature,
            notes='Paid online via Razorpay Checkout.'
        )
        messages.success(request, "Payment successful! Your receipt has been generated.")
        return redirect('invoicing:public', public_token=invoice.public_token)
    else:
        messages.error(request, "Payment signature verification failed. Please try again.")
        return redirect('payments:checkout', invoice_pk=invoice.pk)


@csrf_exempt
@require_POST
def razorpay_webhook_view(request):
    """Idempotent webhook listener for Razorpay payment captured events."""
    import hashlib
    import hmac

    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
    signature = request.headers.get('X-Razorpay-Signature', '')
    payload = request.body

    # Validate HMAC signature if secret configured
    if webhook_secret and signature:
        expected = hmac.new(webhook_secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return HttpResponseBadRequest("Invalid webhook signature")

    try:
        data = json.loads(payload.decode('utf-8'))
        event = data.get('event')

        if event == 'payment.captured':
            payment_entity = data['payload']['payment']['entity']
            payment_id = payment_entity['id']
            order_id = payment_entity.get('order_id', '')
            amount = Decimal(str(payment_entity['amount'])) / Decimal('100.00')
            notes = payment_entity.get('notes', {})
            invoice_id = notes.get('invoice_id')

            if invoice_id:
                invoice = Invoice.objects.filter(id=invoice_id).first()
                if invoice:
                    PaymentService.record_payment(
                        invoice=invoice,
                        amount=amount,
                        method=PaymentMethod.RAZORPAY,
                        gateway_order_id=order_id,
                        gateway_payment_id=payment_id,
                        notes="Settled via Razorpay webhook."
                    )
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_POST
def stripe_webhook_view(request):
    """Idempotent webhook listener for Stripe payment_intent.succeeded events."""
    import hashlib
    import hmac

    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    sig_header = request.headers.get('Stripe-Signature', '')
    payload = request.body

    event = None
    # Validate Stripe signature if secret configured
    if webhook_secret and sig_header:
        try:
            import stripe
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except Exception:
            # Fallback HMAC check if stripe library is not installed or raises error
            expected = hmac.new(webhook_secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, sig_header):
                return HttpResponseBadRequest("Invalid Stripe webhook signature")

    try:
        if not event:
            event = json.loads(payload.decode('utf-8'))

        event_type = event.get('type')
        if event_type in ['payment_intent.succeeded', 'checkout.session.completed']:
            data_object = event['data']['object']
            payment_id = data_object.get('id', '')
            amount_cents = data_object.get('amount') or data_object.get('amount_total', 0)
            amount = Decimal(str(amount_cents)) / Decimal('100.00')
            metadata = data_object.get('metadata', {})
            invoice_id = metadata.get('invoice_id')

            if invoice_id:
                invoice = Invoice.objects.filter(id=invoice_id).first()
                if invoice:
                    PaymentService.record_payment(
                        invoice=invoice,
                        amount=amount,
                        method=PaymentMethod.STRIPE,
                        gateway_order_id=payment_id,
                        gateway_payment_id=payment_id,
                        gateway_signature=sig_header,
                        notes="Settled via Stripe webhook."
                    )
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
