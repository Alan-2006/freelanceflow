from django import forms

from .models import Invoice


class InvoiceCreateForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'client', 'project', 'invoice_number', 'issue_date',
            'due_date', 'currency', 'tax_rate', 'discount_amount',
            'late_fee_rate', 'notes', 'payment_terms'
        ]
        widgets = {
            'client': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'project': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'invoice_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm font-mono'
            }),
            'issue_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'step': '0.01'
            }),
            'discount_amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'step': '0.01'
            }),
            'late_fee_rate': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'step': '0.01'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'rows': 2,
                'placeholder': 'Thank you for your business!'
            }),
            'payment_terms': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'rows': 2,
                'placeholder': 'Payment due within default term window.'
            }),
        }

    def __init__(self, freelancer_profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = freelancer_profile.clients.all()
        self.fields['project'].queryset = freelancer_profile.clients.first().projects.all() if freelancer_profile.clients.exists() else forms.models.ModelChoiceField.queryset
        self.fields['project'].required = False
