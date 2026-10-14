from django import forms

from .models import Payment


class ManualPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'method', 'paid_at', 'proof_file', 'notes']
        widgets = {
            'invoice': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'step': '0.01'
            }),
            'method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'paid_at': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'proof_file': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'rows': 2,
                'placeholder': 'Bank reference ID, wire number, transaction note...'
            }),
        }

    def __init__(self, freelancer_profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['invoice'].queryset = freelancer_profile.invoices.exclude(status='Paid')


class CreditNoteForm(forms.ModelForm):
    class Meta:
        from .models import CreditNote
        model = CreditNote
        fields = ['invoice', 'amount', 'reason', 'issued_date']
        widgets = {
            'invoice': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'step': '0.01'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'rows': 3,
                'placeholder': 'Reason for issuing credit note or refund...'
            }),
            'issued_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
        }

    def __init__(self, freelancer_profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['invoice'].queryset = freelancer_profile.invoices.filter(amount_paid__gt=0)

