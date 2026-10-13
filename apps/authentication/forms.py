from django import forms
from django.contrib.auth import authenticate

from .models import FreelancerProfile, User, UserRole

CURRENCY_CHOICES = [
    ('USD', 'USD - US Dollar ($)'),
    ('EUR', 'EUR - Euro (€)'),
    ('GBP', 'GBP - British Pound (£)'),
    ('INR', 'INR - Indian Rupee (₹)'),
    ('CAD', 'CAD - Canadian Dollar ($)'),
    ('AUD', 'AUD - Australian Dollar ($)'),
]

class FreelancerSignUpForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
        'placeholder': 'Last Name'
    }))
    business_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
        'placeholder': 'Business / Studio Name (optional)'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
        'placeholder': 'alex@studio.com'
    }))
    currency = forms.ChoiceField(choices=CURRENCY_CHOICES, initial='USD', widget=forms.Select(attrs={
        'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
        'placeholder': '••••••••'
    }))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.role = UserRole.FREELANCER
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            profile = user.profile
            business = self.cleaned_data.get('business_name')
            if business:
                profile.business_name = business
            profile.currency = self.cleaned_data.get('currency', 'USD')
            profile.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
        'placeholder': 'you@example.com'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
        'placeholder': '••••••••'
    }))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email', '').strip().lower()
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise forms.ValidationError("Invalid email or password.")
            self.user = user
        return cleaned_data


class FreelancerProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white'
    }))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white'
    }))

    class Meta:
        model = FreelancerProfile
        fields = [
            'business_name', 'logo', 'tax_id', 'address', 'currency',
            'default_payment_terms_days', 'bank_details', 'upi_id', 'brand_color', 'timezone'
        ]
        widgets = {
            'business_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white'}),
            'tax_id': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white', 'placeholder': 'e.g. GSTIN / VAT ID'}),
            'address': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white', 'rows': 3}),
            'currency': forms.Select(choices=CURRENCY_CHOICES, attrs={'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white'}),
            'default_payment_terms_days': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white'}),
            'bank_details': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white', 'rows': 3, 'placeholder': 'Bank Name, Account Number, IFSC/IBAN/SWIFT'}),
            'upi_id': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white', 'placeholder': 'yourname@upi'}),
            'brand_color': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-20 rounded border border-slate-300 dark:border-slate-700 cursor-pointer'}),
            'timezone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.save()
        return profile
