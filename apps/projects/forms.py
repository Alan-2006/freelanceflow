from django import forms

from .models import Attachment, Milestone, Project, Task, TimeEntry

TEMPLATE_CHOICES = [
    ('', 'Start Blank (Custom Milestones)'),
    ('web_development', 'Website Design & Development (4 Milestones)'),
    ('branding', 'Brand Identity & Guidelines (3 Milestones)'),
    ('consulting', 'Sprint Consulting & Audit (2 Milestones)'),
]

class ProjectCreateWizardForm(forms.ModelForm):
    template_type = forms.ChoiceField(
        choices=TEMPLATE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500'
        })
    )

    class Meta:
        model = Project
        fields = [
            'client', 'title', 'description', 'billing_type',
            'budget', 'hourly_rate', 'start_date', 'end_date', 'color_code'
        ]
        widgets = {
            'client': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500',
                'placeholder': 'e.g. NextGen Web App Redesign'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Scope of work, deliverables, and expectations...'
            }),
            'billing_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500'
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500',
                'step': '0.01'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500',
                'step': '0.01'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500'
            }),
            'color_code': forms.TextInput(attrs={
                'type': 'color',
                'class': 'h-10 w-20 rounded border border-slate-300 dark:border-slate-700 cursor-pointer'
            }),
        }

    def __init__(self, freelancer_profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit client selection to the authenticated freelancer's clients
        self.fields['client'].queryset = freelancer_profile.clients.all()


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'milestone', 'status', 'estimated_hours', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'placeholder': 'Task description...'
            }),
            'milestone': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm',
                'step': '0.5'
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm'
            }),
        }

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['milestone'].queryset = project.milestones.all()
        self.fields['milestone'].required = False


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['title', 'description', 'amount', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white',
                'placeholder': 'e.g. Design Prototype'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white',
                'rows': 2,
                'placeholder': 'Deliverable criteria...'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white',
                'step': '0.01'
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white'
            }),
        }


class DeliverableSubmissionForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['deliverable_notes', 'deliverable_file']
        widgets = {
            'deliverable_notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white',
                'rows': 3,
                'placeholder': 'Explain what is ready for review, include staging links, credentials, etc.'
            }),
            'deliverable_file': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white'
            })
        }


class TimeEntryForm(forms.ModelForm):
    hours = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white',
            'placeholder': 'e.g. 2.5',
            'step': '0.25'
        }),
        help_text='Logged duration in hours'
    )

    class Meta:
        model = TimeEntry
        fields = ['project', 'task', 'hourly_rate', 'is_billable', 'note']
        widgets = {
            'project': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white'
            }),
            'task': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white',
                'step': '0.01'
            }),
            'note': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white',
                'placeholder': 'What did you work on?'
            }),
            'is_billable': forms.CheckboxInput(attrs={
                'class': 'rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4'
            })
        }

    def __init__(self, freelancer_profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(client__freelancer=freelancer_profile)
        self.fields['task'].queryset = Task.objects.filter(project__client__freelancer=freelancer_profile)
        self.fields['task'].required = False


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ['file', 'name', 'is_shared_with_client']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white',
                'placeholder': 'e.g. Design Assets v2.zip'
            }),
            'file': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white'
            }),
            'is_shared_with_client': forms.CheckboxInput(attrs={
                'class': 'rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4'
            })
        }

