from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'name', 'company', 'email', 'phone', 'address',
            'currency', 'timezone', 'preferred_channel', 'tags', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
                'placeholder': 'e.g. Sarah Jenkins'
            }),
            'company': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
                'placeholder': 'e.g. Acme Corp / NextGen Digital'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
                'placeholder': 'sarah@acmecorp.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
                'placeholder': '+1 (555) 019-2834'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
                'rows': 2,
                'placeholder': 'Client street address, City, Country'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
                'placeholder': 'USD'
            }),
            'timezone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
                'placeholder': 'America/New_York'
            }),
            'preferred_channel': forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
                'placeholder': 'VIP, Retainer, Referral'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
                'rows': 3,
                'placeholder': 'Internal notes (billing contact preferences, tax exemption notes, etc.)'
            }),
        }
