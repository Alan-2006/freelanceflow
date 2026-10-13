from django.core.management.base import BaseCommand

from apps.reminders.engine import PaymentReminderEngine


class Command(BaseCommand):
    help = 'Evaluate all unpaid invoices and dispatch payment reminders according to rules.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate reminder evaluation without dispatching emails or modifying database records.',
        )
        parser.add_argument(
            '--site-url',
            type=str,
            default='http://127.0.0.1:8000',
            help='Base site URL for public payment links and tracking pixels.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        site_url = options['site_url']

        mode_str = "DRY RUN (Simulated)" if dry_run else "LIVE RUN"
        self.stdout.write(self.style.SUCCESS(f"Starting Payment Reminder Engine: {mode_str}..."))

        stats = PaymentReminderEngine.evaluate_invoices(dry_run=dry_run, site_url=site_url)

        self.stdout.write(f"- Invoices evaluated: {stats['evaluated']}")
        self.stdout.write(f"- Reminders triggered: {stats['dispatched']}")
        self.stdout.write(f"- Skipped (Paused): {stats['skipped_paused']}")
        self.stdout.write(f"- Skipped (Quiet Hours): {stats['skipped_quiet_hours']}")
        self.stdout.write(f"- Skipped (Idempotent / Already Sent): {stats['skipped_idempotent']}")

        for detail in stats['details']:
            if dry_run:
                self.stdout.write(f"  [SIMULATED] -> {detail['invoice']} to {detail['client']} ({detail['tone']})")
            else:
                self.stdout.write(f"  [SENT] -> {detail['invoice']} to {detail['recipient']} ({detail['tone']})")

        self.stdout.write(self.style.SUCCESS("Payment Reminder Engine completed successfully."))
