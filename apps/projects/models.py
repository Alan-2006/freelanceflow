from django.db import models
from django.utils import timezone

from apps.clients.models import Client
from core.models import TimeStampedModel


class ProjectStatus(models.TextChoices):
    DRAFT = 'Draft', 'Draft'
    ACTIVE = 'Active', 'Active'
    ON_HOLD = 'On Hold', 'On Hold'
    COMPLETED = 'Completed', 'Completed'
    CANCELLED = 'Cancelled', 'Cancelled'

class BillingType(models.TextChoices):
    FIXED = 'Fixed', 'Fixed Price'
    HOURLY = 'Hourly', 'Hourly Rate'
    RETAINER = 'Retainer', 'Monthly Retainer'

class MilestoneStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    IN_PROGRESS = 'In Progress', 'In Progress'
    SUBMITTED = 'Submitted', 'Submitted for Review'
    APPROVED = 'Approved', 'Approved'
    REJECTED = 'Rejected', 'Changes Requested'
    PAID = 'Paid', 'Paid'

class TaskStatus(models.TextChoices):
    TODO = 'TODO', 'To Do'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    REVIEW = 'REVIEW', 'In Review'
    DONE = 'DONE', 'Done'


class Project(TimeStampedModel):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.ACTIVE,
        db_index=True
    )
    billing_type = models.CharField(
        max_length=20,
        choices=BillingType.choices,
        default=BillingType.FIXED
    )
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    color_code = models.CharField(max_length=7, default='#6366F1')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.client.company or self.client.name})"

    @property
    def freelancer(self):
        return self.client.freelancer

    @property
    def progress_percentage(self) -> int:
        """Percentage based on approved or paid milestones or completed tasks."""
        total_milestones = self.milestones.count()
        if total_milestones > 0:
            done = self.milestones.filter(status__in=[MilestoneStatus.APPROVED, MilestoneStatus.PAID]).count()
            return int((done / total_milestones) * 100)

        # Fallback to tasks
        total_tasks = self.tasks.count()
        if total_tasks > 0:
            done_tasks = self.tasks.filter(status=TaskStatus.DONE).count()
            return int((done_tasks / total_tasks) * 100)
        return 0

    @property
    def total_billed(self):
        return sum(inv.total_amount for inv in self.invoices.exclude(status='Cancelled'))

    @property
    def total_paid(self):
        return sum(inv.amount_paid for inv in self.invoices.exclude(status='Cancelled'))


class Milestone(TimeStampedModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='milestones'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    due_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=MilestoneStatus.choices,
        default=MilestoneStatus.PENDING,
        db_index=True
    )
    order = models.PositiveIntegerField(default=1)
    deliverable_notes = models.TextField(blank=True, default='', help_text='Deliverable summary or URL')
    deliverable_file = models.FileField(upload_to='deliverables/', blank=True, null=True)
    client_feedback = models.TextField(blank=True, default='', help_text='Client feedback or change requests')
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['order', 'due_date']

    def __str__(self):
        return f"{self.project.title}: {self.title}"


class Task(TimeStampedModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    milestone = models.ForeignKey(
        Milestone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
        db_index=True
    )
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    due_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title


class TimeEntry(TimeStampedModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='time_entries'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_entries'
    )
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    is_billable = models.BooleanField(default=True)
    is_invoiced = models.BooleanField(default=False)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    note = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.project.title} - {self.duration_seconds // 60}m"

    @property
    def billable_amount(self):
        if not self.is_billable:
            return 0
        hours = self.duration_seconds / 3600
        return round(hours * float(self.hourly_rate), 2)


class ActivityLog(TimeStampedModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='activities',
        null=True,
        blank=True
    )
    actor_name = models.CharField(max_length=150)
    action_type = models.CharField(max_length=50)
    details = models.TextField()
    is_client_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.action_type}] {self.actor_name}: {self.details[:40]}"


class Attachment(TimeStampedModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='project_files/')
    name = models.CharField(max_length=255)
    file_size_bytes = models.BigIntegerField(default=0)
    is_shared_with_client = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class MilestoneFeedback(TimeStampedModel):
    milestone = models.ForeignKey(
        Milestone,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )
    author_name = models.CharField(max_length=150)
    is_client = models.BooleanField(default=True)
    feedback_text = models.TextField()
    status_at_time = models.CharField(
        max_length=20,
        choices=MilestoneStatus.choices,
        default=MilestoneStatus.REJECTED
    )
    attachment = models.FileField(upload_to='milestone_feedback/', blank=True, null=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Feedback on {self.milestone.title} by {self.author_name}"
