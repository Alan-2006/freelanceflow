from django import forms

from .models import Invoice, RecurringInvoice


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
        from apps.projects.models import Project
        self.fields['project'].queryset = Project.objects.filter(client__freelancer=freelancer_profile)
        self.fields['project'].required = False


class RecurringInvoiceForm(forms.ModelForm):
    class Meta:
        model = RecurringInvoice
        fields = ['client', 'project', 'title', 'frequency', 'amount', 'next_run_date', 'is_active']
        widgets = {
            'client': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'project': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'placeholder': 'e.g. Monthly Design Retainer'
            }),
            'frequency': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'step': '0.01'
            }),
            'next_run_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4'
            })
        }

    def __init__(self, freelancer_profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = freelancer_profile.clients.all()
        from apps.projects.models import Project
        self.fields['project'].queryset = Project.objects.filter(client__freelancer=freelancer_profile)
        self.fields['project'].required = False


class ProposalCreateForm(forms.ModelForm):
    class Meta:
        from .models import Proposal
        model = Proposal
        fields = [
            'client', 'title', 'proposal_number', 'issue_date',
            'valid_until', 'currency', 'tax_rate', 'overview',
            'scope_of_work', 'terms'
        ]
        widgets = {
            'client': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'placeholder': 'e.g. Website Redesign & Brand Revamp Proposal'
            }),
            'proposal_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm font-mono'
            }),
            'issue_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'valid_until': forms.DateInput(attrs={
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
            'overview': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'rows': 3,
                'placeholder': 'Executive summary and project objectives...'
            }),
            'scope_of_work': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'rows': 4,
                'placeholder': 'Detailed deliverables, inclusions, milestones...'
            }),
            'terms': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'rows': 3,
                'placeholder': 'Validity period, revision limits, payment conditions...'
            }),
        }

    def __init__(self, freelancer_profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = freelancer_profile.clients.all()


