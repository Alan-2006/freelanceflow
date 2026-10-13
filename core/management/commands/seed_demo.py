"""Django management command to seed realistic demo data for FreelanceFlow."""
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.authentication.models import FreelancerProfile, User, UserRole
from apps.clients.models import Client, ReminderChannel
from apps.invoicing.models import Invoice, InvoiceLineItem, InvoiceStatus
from apps.payments.models import Payment, PaymentMethod, PaymentStatus
from apps.projects.models import (
    ActivityLog,
    BillingType,
    Milestone,
    MilestoneStatus,
    Project,
    ProjectStatus,
    Task,
    TaskStatus,
    TimeEntry,
)
from apps.reminders.defaults import DEFAULT_RULES
from apps.reminders.models import ReminderLog, ReminderRule, ReminderTone


class Command(BaseCommand):
    help = "Seed rich, realistic demo data for FreelanceFlow (Projects, Invoices, Milestones, Payments, Reminders)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing demo data before seeding'
        )

    def handle(self, *args, **options):
        clear = options.get('clear', False)
        today = timezone.now().date()
        now = timezone.now()

        demo_email = "demo@freelanceflow.dev"

        if clear:
            self.stdout.write(self.style.WARNING("Clearing existing demo data..."))
            existing_user = User.objects.filter(email=demo_email).first()
            if existing_user:
                if hasattr(existing_user, 'profile'):
                    profile = existing_user.profile
                    # Cascade will delete clients, projects, invoices, payments, reminders
                    profile.clients.all().delete()
                    profile.reminder_rules.all().delete()
                existing_user.delete()
            self.stdout.write(self.style.SUCCESS("Existing demo data cleared."))

        self.stdout.write("Seeding demo Freelancer user...")
        user, created = User.objects.get_or_create(
            email=demo_email,
            defaults={
                'username': 'alex_rivera',
                'first_name': 'Alex',
                'last_name': 'Rivera',
                'role': UserRole.FREELANCER,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        user.set_password("DemoPass123!")
        user.save()

        # Update profile
        profile, _ = FreelancerProfile.objects.get_or_create(user=user)
        profile.business_name = "Rivera Studio & Engineering"
        profile.tax_id = "US-EIN-98-7654321"
        profile.address = "742 Montgomery St, Suite 500, San Francisco, CA 94111"
        profile.currency = "USD"
        profile.default_payment_terms_days = 14
        profile.bank_details = "Silicon Valley Bank\nRouting: 121000358\nAccount: 98765432100\nSWIFT: SVBUS6S"
        profile.upi_id = "alex.rivera@okaxis"
        profile.brand_color = "#4F46E5"
        profile.timezone = "America/Los_Angeles"
        profile.onboarding_completed = True
        profile.save()

        # Ensure default reminder rules
        for rule_def in DEFAULT_RULES:
            ReminderRule.objects.get_or_create(
                freelancer=profile,
                trigger_offset_days=rule_def['trigger_offset_days'],
                defaults={
                    'name': rule_def['name'],
                    'tone': rule_def['tone'],
                    'channel': rule_def['channel'],
                    'subject_template': rule_def['subject_template'],
                    'body_template': rule_def['body_template'],
                    'is_active': True,
                }
            )

        self.stdout.write(self.style.SUCCESS(f"User '{demo_email}' ready (Password: DemoPass123!)"))

        # Seed Clients
        self.stdout.write("Seeding Clients...")
        acme, _ = Client.objects.get_or_create(
            freelancer=profile,
            email="sarah.jenkins@acme-corp.com",
            defaults={
                'name': "Sarah Jenkins",
                'company': "Acme Corporation",
                'phone': "+1 (555) 234-5678",
                'address': "100 Enterprise Way, Floor 12, New York, NY 10001",
                'currency': "USD",
                'preferred_channel': ReminderChannel.EMAIL,
                'reliability_score': 96,
                'tags': "Enterprise, Retainer, VIP",
                'notes': "Enterprise account with net-15 terms. Fast sign-offs and reliable wire transfers."
            }
        )
        acme.get_or_create_portal_token(days_valid=60)

        techstart, _ = Client.objects.get_or_create(
            freelancer=profile,
            email="marcus.chen@techstart.io",
            defaults={
                'name': "Marcus Chen",
                'company': "TechStart Innovations",
                'phone': "+1 (555) 876-5432",
                'address': "450 Mission St, Suite 800, San Francisco, CA 94105",
                'currency': "USD",
                'preferred_channel': ReminderChannel.EMAIL,
                'reliability_score': 82,
                'tags': "Startup, YC-Backed, Fast-Paced",
                'notes': "Series A funded startup. Very agile, occasionally requests milestone scope tweaks."
            }
        )
        techstart.get_or_create_portal_token(days_valid=60)

        horizon, _ = Client.objects.get_or_create(
            freelancer=profile,
            email="elena@horizonagency.co",
            defaults={
                'name': "Elena Rostova",
                'company': "Horizon Creative Agency",
                'phone': "+1 (555) 345-6789",
                'address': "1200 Wilshire Blvd, Los Angeles, CA 90017",
                'currency': "USD",
                'preferred_channel': ReminderChannel.EMAIL,
                'reliability_score': 45,
                'tags': "Agency, Irregular Payments",
                'notes': "Creative partner with cash-flow volatility. Needs automated reminders and follow-up."
            }
        )
        horizon.get_or_create_portal_token(days_valid=60)

        # Seed Projects
        self.stdout.write("Seeding Projects & Milestones...")

        # 1. Acme E-Commerce Platform
        proj_ecommerce, _ = Project.objects.get_or_create(
            client=acme,
            title="NextGen E-Commerce Web Platform",
            defaults={
                'description': "High-performance headless e-commerce store with Next.js frontend, Python microservices, and Stripe checkout.",
                'status': ProjectStatus.ACTIVE,
                'billing_type': BillingType.FIXED,
                'budget': Decimal("18500.00"),
                'hourly_rate': Decimal("100.00"),
                'start_date': today - timedelta(days=45),
                'end_date': today + timedelta(days=45),
                'color_code': "#4F46E5",
            }
        )

        m1_ecom, _ = Milestone.objects.get_or_create(
            project=proj_ecommerce,
            title="Discovery, System Architecture & Database Design",
            defaults={
                'description': "Complete ER diagram, API specification, and technical architecture blueprint.",
                'amount': Decimal("4500.00"),
                'due_date': today - timedelta(days=30),
                'status': MilestoneStatus.PAID,
                'order': 1,
                'deliverable_notes': "Architecture documentation delivered and accepted: https://docs.riverastudio.dev/acme/arch-v1.pdf",
                'approved_at': now - timedelta(days=28),
            }
        )

        m2_ecom, _ = Milestone.objects.get_or_create(
            project=proj_ecommerce,
            title="Core Checkout Microservice & Payment Integration",
            defaults={
                'description': "Stripe Checkout & Elements integration with idempotency handling and webhook dispatchers.",
                'amount': Decimal("6500.00"),
                'due_date': today - timedelta(days=5),
                'status': MilestoneStatus.APPROVED,
                'order': 2,
                'deliverable_notes': "Staging environment deployed with test suite: https://staging-checkout.acme.dev",
                'approved_at': now - timedelta(days=2),
            }
        )

        m3_ecom, _ = Milestone.objects.get_or_create(
            project=proj_ecommerce,
            title="Inventory Management & Real-time Analytics Dashboard",
            defaults={
                'description': "Warehouse stock syncing and executive reporting dashboard with real-time websocket updates.",
                'amount': Decimal("4500.00"),
                'due_date': today + timedelta(days=15),
                'status': MilestoneStatus.IN_PROGRESS,
                'order': 3,
            }
        )

        m4_ecom, _ = Milestone.objects.get_or_create(
            project=proj_ecommerce,
            title="Load Testing, Security Audit & Production Launch",
            defaults={
                'description': "Penetration testing, Redis cache warming, and production launch cutover.",
                'amount': Decimal("3000.00"),
                'due_date': today + timedelta(days=45),
                'status': MilestoneStatus.PENDING,
                'order': 4,
            }
        )

        # Tasks for E-Commerce
        Task.objects.get_or_create(
            project=proj_ecommerce,
            milestone=m1_ecom,
            title="Draft OpenAPI 3.1 specification schema",
            defaults={'status': TaskStatus.DONE, 'estimated_hours': 12, 'order': 1}
        )
        Task.objects.get_or_create(
            project=proj_ecommerce,
            milestone=m2_ecom,
            title="Implement webhook signature verification and idempotency ledger",
            defaults={'status': TaskStatus.DONE, 'estimated_hours': 16, 'order': 2}
        )
        Task.objects.get_or_create(
            project=proj_ecommerce,
            milestone=m3_ecom,
            title="Build warehouse inventory sync Celery background workers",
            defaults={'status': TaskStatus.IN_PROGRESS, 'estimated_hours': 20, 'order': 3}
        )
        Task.objects.get_or_create(
            project=proj_ecommerce,
            milestone=m4_ecom,
            title="Conduct Locust concurrency load tests with 5,000 virtual users",
            defaults={'status': TaskStatus.TODO, 'estimated_hours': 14, 'order': 4}
        )

        # 2. TechStart Brand Identity & Design System
        proj_brand, _ = Project.objects.get_or_create(
            client=techstart,
            title="Brand Identity & Design System 2.0",
            defaults={
                'description': "Complete corporate visual identity refresh, Figma token system, and accessible Tailwind CSS UI library.",
                'status': ProjectStatus.ACTIVE,
                'billing_type': BillingType.FIXED,
                'budget': Decimal("7500.00"),
                'hourly_rate': Decimal("90.00"),
                'start_date': today - timedelta(days=20),
                'end_date': today + timedelta(days=25),
                'color_code': "#EC4899",
            }
        )

        m1_brand, _ = Milestone.objects.get_or_create(
            project=proj_brand,
            title="Visual Identity, Typography & Color Harmony Matrix",
            defaults={
                'description': "Brand guidelines book, primary and secondary palettes, and typography hierarchy.",
                'amount': Decimal("3500.00"),
                'due_date': today - timedelta(days=2),
                'status': MilestoneStatus.SUBMITTED,
                'order': 1,
                'deliverable_notes': "Brand guide presentation and Figma components submitted for client approval: https://figma.com/@rivera/techstart-v2",
            }
        )

        m2_brand, _ = Milestone.objects.get_or_create(
            project=proj_brand,
            title="Tailwind CSS Component Kit & Icon Library",
            defaults={
                'description': "Interactive component library with 40+ responsive widgets and dark mode support.",
                'amount': Decimal("4000.00"),
                'due_date': today + timedelta(days=20),
                'status': MilestoneStatus.IN_PROGRESS,
                'order': 2,
            }
        )

        Task.objects.get_or_create(
            project=proj_brand,
            milestone=m1_brand,
            title="Design dark/light mode accessible contrast palettes",
            defaults={'status': TaskStatus.DONE, 'estimated_hours': 10, 'order': 1}
        )
        Task.objects.get_or_create(
            project=proj_brand,
            milestone=m1_brand,
            title="Build vector icon set (24px grid)",
            defaults={'status': TaskStatus.REVIEW, 'estimated_hours': 15, 'order': 2}
        )
        Task.objects.get_or_create(
            project=proj_brand,
            milestone=m2_brand,
            title="Export design tokens to Tailwind config preset",
            defaults={'status': TaskStatus.IN_PROGRESS, 'estimated_hours': 8, 'order': 3}
        )

        # 3. Horizon Mobile App MVP
        proj_mobile, _ = Project.objects.get_or_create(
            client=horizon,
            title="Fintech Mobile App MVP (React Native)",
            defaults={
                'description': "Cross-platform iOS and Android mobile wallet application with biometric authentication and spending insights.",
                'status': ProjectStatus.ACTIVE,
                'billing_type': BillingType.HOURLY,
                'budget': Decimal("12000.00"),
                'hourly_rate': Decimal("95.00"),
                'start_date': today - timedelta(days=35),
                'end_date': today + timedelta(days=30),
                'color_code': "#F59E0B",
            }
        )

        m1_mobile, _ = Milestone.objects.get_or_create(
            project=proj_mobile,
            title="UX Wireframes & Interaction Flow",
            defaults={
                'description': "Complete user journeys for onboarding, KYC verification, and instant fund transfers.",
                'amount': Decimal("3200.00"),
                'due_date': today - timedelta(days=18),
                'status': MilestoneStatus.REJECTED,
                'order': 1,
                'deliverable_notes': "Initial wireframe deck delivered.",
                'client_feedback': "Please update the KYC flow to support passport upload and biometric FaceID option.",
            }
        )

        m2_mobile, _ = Milestone.objects.get_or_create(
            project=proj_mobile,
            title="Biometric Authentication & Wallet Ledger Engine",
            defaults={
                'description': "Encrypted secure enclave storage and offline transaction caching.",
                'amount': Decimal("4800.00"),
                'due_date': today + timedelta(days=10),
                'status': MilestoneStatus.IN_PROGRESS,
                'order': 2,
            }
        )

        Task.objects.get_or_create(
            project=proj_mobile,
            milestone=m1_mobile,
            title="Revise KYC step 3 with camera passport capture",
            defaults={'status': TaskStatus.IN_PROGRESS, 'estimated_hours': 6, 'order': 1}
        )
        Task.objects.get_or_create(
            project=proj_mobile,
            milestone=m2_mobile,
            title="Wire up React Native Keychain with biometric auth",
            defaults={'status': TaskStatus.TODO, 'estimated_hours': 12, 'order': 2}
        )

        # 4. Acme Cloud Migration (Completed Project)
        proj_cloud, _ = Project.objects.get_or_create(
            client=acme,
            title="Enterprise Cloud Infrastructure Migration",
            defaults={
                'description': "Containerized deployment to AWS ECS with multi-AZ Postgres RDS and automated GitHub Actions CI/CD pipelines.",
                'status': ProjectStatus.COMPLETED,
                'billing_type': BillingType.FIXED,
                'budget': Decimal("15000.00"),
                'hourly_rate': Decimal("110.00"),
                'start_date': today - timedelta(days=90),
                'end_date': today - timedelta(days=10),
                'color_code': "#10B981",
            }
        )

        m1_cloud, _ = Milestone.objects.get_or_create(
            project=proj_cloud,
            title="Terraform Infrastructure as Code & VPC Setup",
            defaults={
                'description': "Automated infrastructure provisioning with zero-trust networking.",
                'amount': Decimal("7500.00"),
                'due_date': today - timedelta(days=60),
                'status': MilestoneStatus.PAID,
                'order': 1,
                'approved_at': now - timedelta(days=58),
            }
        )
        m2_cloud, _ = Milestone.objects.get_or_create(
            project=proj_cloud,
            title="Zero-Downtime Data Migration & Failover Drills",
            defaults={
                'description': "Full PostgreSQL replication and disaster recovery validation.",
                'amount': Decimal("7500.00"),
                'due_date': today - timedelta(days=20),
                'status': MilestoneStatus.PAID,
                'order': 2,
                'approved_at': now - timedelta(days=18),
            }
        )

        # Time Entries (both billed and unbilled)
        self.stdout.write("Seeding Time Entries...")
        TimeEntry.objects.get_or_create(
            project=proj_mobile,
            note="Refining KYC biometric camera capture flow",
            defaults={
                'start_time': now - timedelta(days=1, hours=4),
                'end_time': now - timedelta(days=1),
                'duration_seconds': 14400,  # 4 hours
                'hourly_rate': Decimal("95.00"),
                'is_billable': True,
                'is_invoiced': False,
            }
        )
        TimeEntry.objects.get_or_create(
            project=proj_mobile,
            note="Configuring React Native Push Notifications service worker",
            defaults={
                'start_time': now - timedelta(days=2, hours=3),
                'end_time': now - timedelta(days=2),
                'duration_seconds': 10800,  # 3 hours
                'hourly_rate': Decimal("95.00"),
                'is_billable': True,
                'is_invoiced': False,
            }
        )
        TimeEntry.objects.get_or_create(
            project=proj_brand,
            note="Design token export and contrast audits",
            defaults={
                'start_time': now - timedelta(days=4, hours=5),
                'end_time': now - timedelta(days=4),
                'duration_seconds': 18000,  # 5 hours
                'hourly_rate': Decimal("90.00"),
                'is_billable': True,
                'is_invoiced': True,
            }
        )

        # Seed Invoices in Diverse States
        self.stdout.write("Seeding Invoices, Line Items, and Payments...")

        # 1. PAID Invoice (Acme E-Com Discovery)
        inv1, _ = Invoice.objects.get_or_create(
            freelancer=profile,
            invoice_number="INV-2026-0001",
            defaults={
                'client': acme,
                'project': proj_ecommerce,
                'issue_date': today - timedelta(days=35),
                'due_date': today - timedelta(days=21),
                'status': InvoiceStatus.PAID,
                'subtotal': Decimal("4500.00"),
                'tax_rate': Decimal("10.00"),
                'tax_amount': Decimal("450.00"),
                'total_amount': Decimal("4950.00"),
                'amount_paid': Decimal("4950.00"),
                'currency': "USD",
                'notes': "Thank you for partnering with Rivera Studio!",
                'payment_terms': "Net 14 days from issue date.",
                'viewed_at': now - timedelta(days=34),
            }
        )
        InvoiceLineItem.objects.get_or_create(
            invoice=inv1,
            description="Discovery, System Architecture & Database Design",
            defaults={
                'quantity': Decimal("1.00"),
                'unit_price': Decimal("4500.00"),
                'tax_rate': Decimal("10.00"),
                'total': Decimal("4950.00"),
                'milestone': m1_ecom,
            }
        )
        Payment.objects.get_or_create(
            invoice=inv1,
            amount=Decimal("4950.00"),
            defaults={
                'currency': "USD",
                'method': PaymentMethod.RAZORPAY,
                'status': PaymentStatus.COMPLETED,
                'gateway_order_id': "order_live_acme001",
                'gateway_payment_id': "pay_acme_settled_001",
                'paid_at': now - timedelta(days=24),
                'notes': "Automatic settlement via Razorpay Card",
            }
        )

        # 2. PAID Invoice (Acme Cloud Migration)
        inv2, _ = Invoice.objects.get_or_create(
            freelancer=profile,
            invoice_number="INV-2026-0002",
            defaults={
                'client': acme,
                'project': proj_cloud,
                'issue_date': today - timedelta(days=25),
                'due_date': today - timedelta(days=11),
                'status': InvoiceStatus.PAID,
                'subtotal': Decimal("15000.00"),
                'tax_rate': Decimal("10.00"),
                'tax_amount': Decimal("1500.00"),
                'total_amount': Decimal("16500.00"),
                'amount_paid': Decimal("16500.00"),
                'currency': "USD",
                'notes': "Full settlement for AWS Cloud Migration.",
                'payment_terms': "Net 14 days.",
                'viewed_at': now - timedelta(days=24),
            }
        )
        InvoiceLineItem.objects.get_or_create(
            invoice=inv2,
            description="Terraform AWS IaC & Zero-Downtime DB Migration",
            defaults={
                'quantity': Decimal("1.00"),
                'unit_price': Decimal("15000.00"),
                'tax_rate': Decimal("10.00"),
                'total': Decimal("16500.00"),
                'milestone': m1_cloud,
            }
        )
        Payment.objects.get_or_create(
            invoice=inv2,
            amount=Decimal("16500.00"),
            defaults={
                'currency': "USD",
                'method': PaymentMethod.MANUAL_BANK,
                'status': PaymentStatus.COMPLETED,
                'paid_at': now - timedelta(days=12),
                'notes': "Wire transfer confirmed by Silicon Valley Bank",
            }
        )

        # 3. PARTIALLY PAID Invoice (Acme E-Com Checkout)
        inv3, _ = Invoice.objects.get_or_create(
            freelancer=profile,
            invoice_number="INV-2026-0003",
            defaults={
                'client': acme,
                'project': proj_ecommerce,
                'issue_date': today - timedelta(days=10),
                'due_date': today + timedelta(days=4),
                'status': InvoiceStatus.PARTIALLY_PAID,
                'subtotal': Decimal("6500.00"),
                'tax_rate': Decimal("10.00"),
                'tax_amount': Decimal("650.00"),
                'total_amount': Decimal("7150.00"),
                'amount_paid': Decimal("3500.00"),
                'currency': "USD",
                'notes': "Milestone 2 deliverable: 50% advance deposit received.",
                'payment_terms': "Net 14 days.",
                'viewed_at': now - timedelta(days=8),
            }
        )
        InvoiceLineItem.objects.get_or_create(
            invoice=inv3,
            description="Core Checkout Microservice & Payment Integration",
            defaults={
                'quantity': Decimal("1.00"),
                'unit_price': Decimal("6500.00"),
                'tax_rate': Decimal("10.00"),
                'total': Decimal("7150.00"),
                'milestone': m2_ecom,
            }
        )
        Payment.objects.get_or_create(
            invoice=inv3,
            amount=Decimal("3500.00"),
            defaults={
                'currency': "USD",
                'method': PaymentMethod.MANUAL_BANK,
                'status': PaymentStatus.COMPLETED,
                'paid_at': now - timedelta(days=5),
                'notes': "Partial installment 1 of 2",
            }
        )

        # 4. VIEWED Invoice (TechStart Brand Identity)
        inv4, _ = Invoice.objects.get_or_create(
            freelancer=profile,
            invoice_number="INV-2026-0004",
            defaults={
                'client': techstart,
                'project': proj_brand,
                'issue_date': today - timedelta(days=7),
                'due_date': today + timedelta(days=7),
                'status': InvoiceStatus.VIEWED,
                'subtotal': Decimal("3500.00"),
                'tax_rate': Decimal("10.00"),
                'tax_amount': Decimal("350.00"),
                'total_amount': Decimal("3850.00"),
                'amount_paid': Decimal("0.00"),
                'currency': "USD",
                'notes': "Milestone 1 Brand Guidelines deliverable.",
                'payment_terms': "Net 14 days.",
                'viewed_at': now - timedelta(days=2),
            }
        )
        InvoiceLineItem.objects.get_or_create(
            invoice=inv4,
            description="Visual Identity, Typography & Color Harmony Matrix",
            defaults={
                'quantity': Decimal("1.00"),
                'unit_price': Decimal("3500.00"),
                'tax_rate': Decimal("10.00"),
                'total': Decimal("3850.00"),
                'milestone': m1_brand,
            }
        )

        # 5. OVERDUE Invoice 1 (Horizon Mobile Wireframing) - 16 days overdue
        inv5, _ = Invoice.objects.get_or_create(
            freelancer=profile,
            invoice_number="INV-2026-0005",
            defaults={
                'client': horizon,
                'project': proj_mobile,
                'issue_date': today - timedelta(days=30),
                'due_date': today - timedelta(days=16),
                'status': InvoiceStatus.OVERDUE,
                'subtotal': Decimal("3200.00"),
                'tax_rate': Decimal("10.00"),
                'tax_amount': Decimal("320.00"),
                'late_fee_rate': Decimal("5.00"),
                'late_fee_amount': Decimal("160.00"),
                'total_amount': Decimal("3680.00"),
                'amount_paid': Decimal("0.00"),
                'currency': "USD",
                'notes': "Immediate payment requested to continue sprint roadmap.",
                'payment_terms': "Net 14 days. 5% late fee applies to overdue balances.",
                'viewed_at': now - timedelta(days=28),
            }
        )
        InvoiceLineItem.objects.get_or_create(
            invoice=inv5,
            description="UX Wireframes & Interaction Flow Specification",
            defaults={
                'quantity': Decimal("1.00"),
                'unit_price': Decimal("3200.00"),
                'tax_rate': Decimal("10.00"),
                'total': Decimal("3520.00"),
                'milestone': m1_mobile,
            }
        )

        # 6. OVERDUE Invoice 2 (Horizon Agency Retainer) - 35 days overdue
        inv6, _ = Invoice.objects.get_or_create(
            freelancer=profile,
            invoice_number="INV-2026-0006",
            defaults={
                'client': horizon,
                'issue_date': today - timedelta(days=49),
                'due_date': today - timedelta(days=35),
                'status': InvoiceStatus.OVERDUE,
                'subtotal': Decimal("1800.00"),
                'tax_rate': Decimal("0.00"),
                'tax_amount': Decimal("0.00"),
                'late_fee_rate': Decimal("5.00"),
                'late_fee_amount': Decimal("90.00"),
                'total_amount': Decimal("1890.00"),
                'amount_paid': Decimal("0.00"),
                'currency': "USD",
                'notes': "Final notice regarding outstanding monthly design retainer.",
                'payment_terms': "Immediate settlement required.",
                'viewed_at': now - timedelta(days=40),
            }
        )
        InvoiceLineItem.objects.get_or_create(
            invoice=inv6,
            description="Monthly UI/UX Retainer & Production Support",
            defaults={
                'quantity': Decimal("1.00"),
                'unit_price': Decimal("1800.00"),
                'tax_rate': Decimal("0.00"),
                'total': Decimal("1800.00"),
            }
        )

        # 7. DRAFT Invoice
        inv7, _ = Invoice.objects.get_or_create(
            freelancer=profile,
            invoice_number="INV-2026-0007",
            defaults={
                'client': techstart,
                'project': proj_brand,
                'issue_date': today,
                'due_date': today + timedelta(days=14),
                'status': InvoiceStatus.DRAFT,
                'subtotal': Decimal("4000.00"),
                'tax_rate': Decimal("10.00"),
                'tax_amount': Decimal("400.00"),
                'total_amount': Decimal("4400.00"),
                'amount_paid': Decimal("0.00"),
                'currency': "USD",
                'notes': "Draft invoice for upcoming Component Kit milestone.",
                'payment_terms': "Net 14 days.",
            }
        )
        InvoiceLineItem.objects.get_or_create(
            invoice=inv7,
            description="Tailwind CSS Component Kit & Icon Library",
            defaults={
                'quantity': Decimal("1.00"),
                'unit_price': Decimal("4000.00"),
                'tax_rate': Decimal("10.00"),
                'total': Decimal("4400.00"),
                'milestone': m2_brand,
            }
        )

        # Seed Reminder Logs with Open/Click events
        self.stdout.write("Seeding Reminder Logs & Email Tracking...")
        rule_friendly = ReminderRule.objects.filter(freelancer=profile, tone=ReminderTone.FRIENDLY).first()
        rule_polite = ReminderRule.objects.filter(freelancer=profile, tone=ReminderTone.POLITE_NUDGE).first()
        rule_firm = ReminderRule.objects.filter(freelancer=profile, tone=ReminderTone.FIRM).first()
        rule_final = ReminderRule.objects.filter(freelancer=profile, tone=ReminderTone.FINAL_NOTICE).first()

        # Logs for inv5 (Horizon)
        if rule_friendly:
            log1, _ = ReminderLog.objects.get_or_create(
                invoice=inv5,
                rule=rule_friendly,
                scheduled_date=today - timedelta(days=19),
                defaults={
                    'channel': 'EMAIL',
                    'tone': ReminderTone.FRIENDLY,
                    'recipient': horizon.email,
                    'subject': f"Friendly reminder: Upcoming invoice {inv5.invoice_number}",
                    'message_body': f"Hi {horizon.name}, your invoice {inv5.invoice_number} is approaching due date.",
                    'sent_at': now - timedelta(days=19, hours=3),
                    'opened': True,
                    'opened_at': now - timedelta(days=19, hours=1),
                    'clicked': False,
                }
            )

        if rule_polite:
            log2, _ = ReminderLog.objects.get_or_create(
                invoice=inv5,
                rule=rule_polite,
                scheduled_date=today - timedelta(days=16),
                defaults={
                    'channel': 'EMAIL',
                    'tone': ReminderTone.POLITE_NUDGE,
                    'recipient': horizon.email,
                    'subject': f"Invoice {inv5.invoice_number} is due today",
                    'message_body': f"Hi {horizon.name}, just a friendly nudge that invoice {inv5.invoice_number} is due today.",
                    'sent_at': now - timedelta(days=16, hours=4),
                    'opened': True,
                    'opened_at': now - timedelta(days=16, hours=2),
                    'clicked': True,
                    'clicked_at': now - timedelta(days=16, hours=2, minutes=10),
                }
            )

        if rule_firm:
            log3, _ = ReminderLog.objects.get_or_create(
                invoice=inv5,
                rule=rule_firm,
                scheduled_date=today - timedelta(days=13),
                defaults={
                    'channel': 'EMAIL',
                    'tone': ReminderTone.FIRM,
                    'recipient': horizon.email,
                    'subject': f"Payment overdue: Invoice {inv5.invoice_number}",
                    'message_body': f"Hi {horizon.name}, payment for invoice {inv5.invoice_number} is now overdue. Please settle today.",
                    'sent_at': now - timedelta(days=13, hours=5),
                    'opened': True,
                    'opened_at': now - timedelta(days=12, hours=14),
                    'clicked': False,
                }
            )

        if rule_final:
            log4, _ = ReminderLog.objects.get_or_create(
                invoice=inv6,
                rule=rule_final,
                scheduled_date=today - timedelta(days=21),
                defaults={
                    'channel': 'EMAIL',
                    'tone': ReminderTone.FINAL_NOTICE,
                    'recipient': horizon.email,
                    'subject': f"FINAL NOTICE: Urgent settlement required for {inv6.invoice_number}",
                    'message_body': f"Dear {horizon.name}, this is our final notice regarding overdue invoice {inv6.invoice_number}.",
                    'sent_at': now - timedelta(days=21, hours=6),
                    'opened': False,
                    'clicked': False,
                }
            )

        # Seed Activity Logs
        ActivityLog.objects.get_or_create(
            project=proj_ecommerce,
            actor_name="Alex Rivera",
            action_type="MILESTONE_SUBMITTED",
            defaults={'details': "Submitted Milestone 2: Core Checkout Microservice with demo staging link.", 'is_client_visible': True}
        )
        ActivityLog.objects.get_or_create(
            project=proj_ecommerce,
            actor_name="Sarah Jenkins",
            action_type="MILESTONE_APPROVED",
            defaults={'details': "Approved Milestone 2 and authorized partial payment transfer.", 'is_client_visible': True}
        )
        ActivityLog.objects.get_or_create(
            project=proj_mobile,
            actor_name="Elena Rostova",
            action_type="CHANGES_REQUESTED",
            defaults={'details': "Requested updates to KYC onboarding screens to add biometric flow.", 'is_client_visible': True}
        )

        self.stdout.write(self.style.SUCCESS("\n========================================================"))
        self.stdout.write(self.style.SUCCESS("Demo database successfully seeded!"))
        self.stdout.write(self.style.SUCCESS("--------------------------------------------------------"))
        self.stdout.write(f"Freelancer Login:  {demo_email}")
        self.stdout.write("Password:          DemoPass123!")
        self.stdout.write("Clients:           3 (Acme Corp, TechStart, Horizon)")
        self.stdout.write("Projects:          4 (E-Commerce, Brand Identity, Mobile App, Cloud Migration)")
        self.stdout.write("Invoices:          7 (Paid, Partially Paid, Viewed, Overdue, Draft)")
        self.stdout.write(f"Client Portal 1:   /portal/{acme.portal_token}/ (Acme Corp)")
        self.stdout.write(f"Client Portal 2:   /portal/{techstart.portal_token}/ (TechStart)")
        self.stdout.write(f"Client Portal 3:   /portal/{horizon.portal_token}/ (Horizon)")
        self.stdout.write(self.style.SUCCESS("========================================================\n"))
