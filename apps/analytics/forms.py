from django import forms

from apps.projects.models import Project

from .models import Expense


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['vendor', 'category', 'amount', 'currency', 'date', 'project', 'description', 'receipt_file', 'is_tax_deductible']
        widgets = {
            'vendor': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'placeholder': 'e.g. AWS, Figma, Google Workspace'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm font-mono',
                'step': '0.01'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'project': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'description': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'placeholder': 'What was this expense for?'
            }),
            'receipt_file': forms.FileInput(attrs={
                'class': 'w-full px-3 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs'
            }),
            'is_tax_deductible': forms.CheckboxInput(attrs={
                'class': 'rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4'
            })
        }

    def __init__(self, freelancer_profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(client__freelancer=freelancer_profile)
        self.fields['project'].required = False
