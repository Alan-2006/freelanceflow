# FreelanceFlow

> **Production-Grade Freelancer-to-Client Project & Invoicing Tracker with Milestone Deliverables and Automated Payment Reminders.**

![Django](https://img.shields.io/badge/Django-5.1-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![HTMX](https://img.shields.io/badge/HTMX-336699?style=for-the-badge)
![Alpine.js](https://img.shields.io/badge/Alpine.js-8BC0D0?style=for-the-badge&logo=alpinedotjs&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-30%20Passed%20(100%25)-success?style=for-the-badge)

---

## 🌟 Key Features

### 1. 🎯 Milestone-Driven Project Lifecycle
- **Project Launcher Wizard**: 4-step interactive wizard with industry presets (*Web Development*, *Brand Identity*, *Mobile App*, *Retainer*).
- **Interactive Kanban Board**: Move tasks between `To Do`, `In Progress`, `In Review`, and `Done` using drag-and-drop or fast HTMX clicks with zero page reload.
- **Milestone Deliverable Approvals**: Submit deliverable URLs/files directly to clients. Payment release unlocks automatically when the client signs off.

### 2. 🔐 Frictionless Magic-Link Client Portal
- **Zero-Password Client Access**: Clients access their dedicated dashboard through cryptographically signed, timestamped magic links (`/portal/<token>/`).
- **Interactive Review Screen**: Clients review project deliverables, download files, approve milestones with celebratory confetti animations, or submit detailed change requests.
- **Client Reliability Scoring**: Clients are dynamically categorized as **Gold**, **Silver**, **Bronze**, or **At-Risk** based on historical payment performance.

### 3. ⚡ Live Split-Screen Invoice Builder & Vector PDF
- **Reactive Dual-Pane Editor**: Edit line items, taxes, discounts, and late fees on the left while watching the pixel-perfect invoice update in real time on the right via Alpine.js.
- **One-Click Timesheet Conversion**: Convert unbilled tracked hours directly into billable invoice line items.
- **Dynamic QR Codes**: Instant UPI QR codes and payment gateway links embedded on invoices.
- **Vector PDF Generation**: High-fidelity invoice PDFs rendered via WeasyPrint with automatic ReportLab fallback.

### 4. 🤖 Autonomous Payment Reminder Engine
- **Tone Escalation State Machine**:
  - `Friendly` (-3 days before due date)
  - `Polite Nudge` (On due date)
  - `Firm` (+3 to +7 days overdue)
  - `Final Notice` (+14 days overdue)
- **Timezone & Quiet Hours Protection**: Reminders are automatically suppressed before 9:00 AM and after 7:00 PM in the client's local timezone.
- **Email Open & Click Tracking**: 1x1 transparent tracking pixel records `opened_at` events, and payment action links record `clicked_at` timestamps.
- **Strict Idempotency Guard**: Prevents duplicate reminder delivery regardless of execution frequency.

### 5. 📊 Executive Analytics & Cash-Flow Runway
- **Visual Collection Health Gauge**: Real-time gauge meter indicating payment recovery efficiency over the last 90 days.
- **Aging Report Buckets**: Invoices bucketed into `0-30`, `31-60`, `61-90`, and `90+` days.
- **Cash Runway Forecast**: 30, 60, and 90-day cash projections based on milestone deliverables and recurring retainers.
- **CSV Data Exports**: One-click data exports for tax compliance and accounting.

### 6. 🚀 Creative Modern UI & PWA Ready
- **Glassmorphic Modern UI**: Curated indigo/violet theme with seamless Dark/Light mode switching.
- **Persistent Global Stopwatch**: Track billable time from anywhere in the app with start/stop/resume timer controls.
- **Quick Command Palette (`Ctrl + K`)**: Instant search and navigation across all clients, projects, and invoices.
- **Keyboard Shortcuts (`?`)**: Quick hotkeys for power users (`n` for new project, `t` for timer, `/` for search).
- **Progressive Web App (PWA)**: Offline service worker and installable web manifest.
- **RESTful API with Interactive Swagger/Docs**: Token-authenticated DRF API endpoints at `/api/v1/` with visual documentation at `/api/docs/`.

---

## 🏗️ System Architecture

```mermaid
graph TD
    ClientBrowser[Client Web Browser<br/>Tailwind CSS + Alpine.js + HTMX] -->|HTTP / REST| DjangoServer[Django 5.1 Application Server]
    
    subgraph Core Services
        DjangoServer --> AuthSvc[Authentication & Role Guard]
        DjangoServer --> ProjectSvc[Project & Milestone Service]
        DjangoServer --> InvoiceSvc[Invoice Calculation & PDF Service]
        DjangoServer --> PaymentSvc[Payment Settlement & Idempotency]
        DjangoServer --> PortalSvc[Magic Link Portal Service]
        DjangoServer --> ReminderEngine[Autonomous Reminder Engine]
        DjangoServer --> AnalyticsSvc[Runway & Financial Analytics]
    end

    subgraph Background Processing
        DjangoServer -.-> CeleryWorker[Celery Async Worker]
        CeleryWorker <--> RedisBroker[(Redis Message Broker)]
        DjangoServer -.-> APScheduler[APScheduler Fallback]
    end

    subgraph Data Persistence
        AuthSvc --> DB[(PostgreSQL 16 / SQLite)]
        ProjectSvc --> DB
        InvoiceSvc --> DB
        PaymentSvc --> DB
        ReminderEngine --> DB
    end
```

---

## ⚡ Quickstart Guide

### Option 1: Docker Compose (Recommended for Production & Viva)

The complete stack (Django, PostgreSQL, Redis, Celery Worker, and Celery Beat) can be booted with a single command:

```bash
# 1. Clone the repository
git clone https://github.com/your-username/freelanceflow.git
cd freelanceflow

# 2. Boot all services with Docker Compose
docker compose up -d --build

# 3. Access the application
# Web App:          http://localhost:8000/
# API Documentation: http://localhost:8000/api/docs/
```

*Note: The Docker entrypoint automatically applies database migrations and seeds rich demo data.*

---

### Option 2: Local Python Development Setup

#### Prerequisites
- Python 3.12 or 3.14
- Virtual environment tool (`venv`)

#### 1. Setup Virtual Environment
```bash
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate
```

#### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Initialize Database & Seed Demo Data
```bash
python manage.py migrate
python manage.py seed_demo --clear
```

#### 4. Run Development Server
```bash
python manage.py runserver
```

Open your browser to [http://localhost:8000/](http://localhost:8000/).

---

## 🔑 Demo Credentials & Quick Links

Running `python manage.py seed_demo --clear` generates a complete, live sandbox environment:

| Role | Username / Email | Password | Access URL |
| :--- | :--- | :--- | :--- |
| **Freelancer Admin** | `demo@freelanceflow.dev` | `DemoPass123!` | [http://localhost:8000/auth/login/](http://localhost:8000/auth/login/) |
| **Acme Corp Portal** | *No password required* | *(Token Access)* | `/portal/<acme_token>/` |
| **TechStart Portal** | *No password required* | *(Token Access)* | `/portal/<techstart_token>/` |
| **Horizon Agency Portal** | *No password required* | *(Token Access)* | `/portal/<horizon_token>/` |
| **API Documentation** | *Authenticated / Public* | *(Interactive)* | [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/) |

---

## 🧪 Testing & Quality Assurance

FreelanceFlow includes 30 automated test cases with 100% pass rate:

```bash
# Run the complete test suite
pytest -v

# Run with test coverage report
pytest --cov=apps --cov=core
```

### Test Coverage Highlights
- ✅ **Authentication**: User registration, role assignments, profile signals, login/logout, theme toggle.
- ✅ **Clients**: CRUD operations, portal token creation, live search & tag filtering.
- ✅ **Projects & Kanban**: 4-step wizard creation, HTMX task status updates, deliverable submissions.
- ✅ **Client Portal**: Magic link authentication, access control decorators, milestone approvals, change requests.
- ✅ **Invoicing**: Auto-numbering sequential formats, tax/discount calculation, time-entry conversion, PDF rendering.
- ✅ **Payments**: Payment settlement state transitions, double-credit idempotency protection, gateway interface verification.
- ✅ **Reminder Engine**: Variable interpolation, quiet hours enforcement, duplicate delivery prevention, pixel open/click tracking.
- ✅ **Analytics**: KPI aggregation, aging buckets, CSV exports.
- ✅ **REST API**: Client and project viewsets, pagination, schema introspection.

---

## 📁 Project Structure

```
d:/ff/pyhtonpro/
├── apps/
│   ├── analytics/           # KPI dashboards, cash-flow forecast, aging reports
│   ├── api/                 # DRF serializers, viewsets, interactive API docs
│   ├── authentication/      # Custom User model, FreelancerProfile, auth views
│   ├── clients/             # Client management, reliability scores, portal tokens
│   ├── invoicing/           # Split-screen builder, PDF generator, QR generator
│   ├── payments/            # Razorpay & Mock gateways, settlement service
│   ├── portal/              # Magic-link client portal, deliverable review
│   ├── projects/            # Project wizard, Kanban board, Milestones, Timers
│   └── reminders/           # Escalating engine, quiet hours, email tracking
├── config/
│   ├── settings/            # Modular settings (base.py, dev.py, prod.py)
│   ├── celery.py            # Celery async task queue configuration
│   └── urls.py              # Root routing table
├── core/
│   ├── management/commands/ # Custom CLI commands (seed_demo, run_reminders)
│   ├── models.py            # TimeStampedModel abstract base
│   └── utils.py             # Cryptographic token generators
├── docs/
│   └── VIVA_NOTES.md        # Comprehensive viva defense guide & Q&A
├── static/
│   ├── css/custom.css       # Custom animations and scrollbars
│   └── pwa/                 # Service worker & manifest.json
├── templates/               # Responsive HTML templates with HTMX partials
├── tests/                   # Pytest automated test suite
├── Dockerfile               # Multi-stage production container
├── docker-compose.yml       # Orchestration for web, db, redis, celery
└── requirements.txt         # Pinned Python package dependencies
```

---

## 🎓 Viva Defense & Technical Documentation

For an in-depth code walk-through, architecture justification, database normalization proofs, and 15+ answered viva questions, refer to the [Viva Defense Kit](file:///d:/ff/pyhtonpro/docs/VIVA_NOTES.md).

---

## 📄 License
This project is licensed under the MIT License. Developed as a final-year engineering capstone project.
