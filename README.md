# 🐍 memora‑django

[![PyPI version](https://badge.fury.io/py/memora-django.svg)](https://badge.fury.io/py/memora-django)
[![Python Versions](https://img.shields.io/pypi/pyversions/memora-django.svg)](https://pypi.org/project/memora-django)
[![Django Versions](https://img.shields.io/badge/django-5.0%20%7C%204.2-blue.svg)](https://www.djangoproject.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/yourusername/memora/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/memora/actions)

**memora‑django** is a reusable Django backend for the **Memora** local‑first note‑taking platform. It provides a full REST API with AI integration, Git sync, and dozens of enterprise features out of the box.

Use it as a **standalone backend** or pair it with the **Gotion Go microservice** to offload heavy tasks like AI summarisation, full‑text search, and image processing. Together they form a **hybrid architecture** that gives you the rapid development of Django and the raw performance of Go where it matters.

---

## 🧩 Hybrid Architecture with Gotion

memora‑django and Gotion are designed to complement each other.

|                  | memora‑django (Python) | Gotion (Go)         |
|------------------|------------------------|---------------------|
| **Primary role** | Web API, user management, file handling, task orchestration | Heavy AI, full‑text search, image processing, background jobs |
| **Strengths**    | Rich ecosystem, admin, ORM, rapid prototyping | Concurrency, low memory, sub‑millisecond operations |
| **Typical use**  | Handles all CRUD, authentication, webhooks, and standard API | Offloaded by Django for CPU‑intensive or latency‑critical tasks |

### How they work together

1. **Django** receives the user request.
2. If the request involves a heavy task (e.g., AI summarisation of a large note, OCR on an uploaded image, or a complex full‑text search), Django **enqueues a job** (via Celery + Redis) that calls the Gotion microservice.
3. **Gotion** processes the task quickly and returns the result, which Django stores and returns to the client.

You get the best of both worlds: Django’s mature ecosystem for rapid development and Go’s raw speed for heavy lifting.

---

## 🚀 Deployment Topologies

### Option 1: Django‑only (light / medium loads)

For moderate traffic, memora‑django handles everything itself. The built‑in Celery workers process background tasks in Python.

```
┌──────────┐     HTTP      ┌─────────────────┐
│  Client  │ ──────────────│  memora‑django   │
└──────────┘               │  (Celery worker) │
                            └─────────────────┘
```

### Option 2: Hybrid (heavy loads)

Add Gotion as a sidecar microservice. Django offloads heavy tasks to Gotion via Celery + Redis.

```
┌──────────┐     HTTP      ┌─────────────────┐     Redis      ┌──────────┐
│  Client  │ ──────────────│  memora‑django   │ ──────────────│  Gotion  │
└──────────┘               │  (Celery worker) │               │  (Go)    │
                            └─────────────────┘               └──────────┘
```

### Option 3: Full Microservices

Use a dedicated API gateway (e.g., Nginx, Traefik) to route directly to Gotion for search or AI endpoints, while Django handles the rest.

---

## 📦 Installation

```bash
pip install memora-django
```

Requires **Python 3.10+** and **Django 5.0+**.

---

## 🏁 Quick Start

### 1. Add the apps to `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'corsheaders',
    'markdownx',
    'apps.notes',
    'apps.ai_service',
    'apps.git_service',
    'apps.users',
]
```

### 2. Include the URLs

```python
from django.urls import include, path

urlpatterns = [
    path('api/v1/', include('apps.notes.urls')),
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/ai/', include('apps.ai_service.urls')),
]
```

### 3. Configure middleware

```python
MIDDLEWARE = [
    # ...
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Set environment variables

```bash
DJANGO_SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...
```

---

## ⚙️ Configuration

All settings can be configured via environment variables or directly in Django’s `settings.py`.

### Core

| Variable              | Default         | Description                       |
|-----------------------|-----------------|-----------------------------------|
| `DJANGO_SECRET_KEY`   | (required)      | Django secret key                 |
| `DEBUG`               | `False`         | Enable debug mode                 |
| `ALLOWED_HOSTS`       | `*`             | Comma‑separated list of hosts     |
| `DATABASE_URL`        | `sqlite:///db.sqlite3` | Database connection         |

### AI (OpenAI)

| Variable              | Default | Description            |
|-----------------------|---------|------------------------|
| `OPENAI_API_KEY`      |         | OpenAI API key         |
| `ANTHROPIC_API_KEY`   |         | Anthropic API key (optional) |
| `AI_MODEL`            | `gpt-3.5-turbo` | Default AI model   |

### Git & GitHub

| Variable              | Default | Description                |
|-----------------------|---------|----------------------------|
| `GITHUB_USERNAME`     |         | GitHub username            |
| `GITHUB_TOKEN`        |         | Personal access token      |
| `GITHUB_REPO`         |         | Repository name            |
| `NOTES_DIR`           | `./data/notes_repo` | Local Git repo path  |

### Storage

| Variable              | Default | Description                        |
|-----------------------|---------|------------------------------------|
| `DEFAULT_FILE_STORAGE`| `django.core.files.storage.FileSystemStorage` | Storage backend |
| `AWS_ACCESS_KEY_ID`   |         | S3 / R2 access key                |
| `AWS_SECRET_ACCESS_KEY` |       | S3 / R2 secret key                |
| `AWS_STORAGE_BUCKET_NAME` |     | Bucket name                       |

### Security

| Variable              | Default | Description                     |
|-----------------------|---------|---------------------------------|
| `JWT_SECRET`          | `change-me` | JWT signing key            |
| `JWT_EXPIRATION`      | `24h`   | Access token lifetime           |
| `RATE_LIMIT`          | `100`   | Requests per minute per IP      |
| `CORS_ALLOWED_ORIGINS`| `http://localhost:3000` | Allowed origins   |

### Gotion Integration

| Variable                | Default | Description                              |
|-------------------------|---------|------------------------------------------|
| `GOTION_ENABLED`        | `False` | Enable offloading to Gotion              |
| `GOTION_BASE_URL`       | `http://localhost:8080` | Gotion API base URL             |
| `GOTION_AUTH_TOKEN`     |         | Shared JWT or API key for internal calls |

---

## 🧵 Offloading to Gotion

When `GOTION_ENABLED=True`, memora‑django will automatically delegate the following operations to Gotion:

- **AI summarisation** – large text summarisation uses Gotion’s low‑latency AI service
- **Full‑text search** – queries bypass Django’s ORM and use Bleve via Gotion
- **Image OCR / processing** – CPU‑intensive image tasks are sent to Gotion
- **PDF export** – heavy PDF generation is handled by Gotion’s chromedp worker

### How to enable

1. Start a Gotion instance (see [Gotion README](https://github.com/yourusername/gotion)).
2. Set the environment variables above.
3. memora‑django will automatically route eligible tasks to Gotion. No code changes needed.

---

## 📡 API Reference

Interactive Swagger documentation is available at:

```
http://localhost:8000/api/v1/docs/
```

### Key Endpoints

| Group         | Base Path                     | Description |
|---------------|-------------------------------|-------------|
| Notes         | `/api/v1/notes/`              | CRUD, archive, favorite, versions, bulk, export, calendar |
| AI            | `/api/v1/ai/`                 | Summarize, generate tags, improve writing, analyze |
| Comments      | `/api/v1/notes/{id}/comments/`| Threaded comments |
| Attachments   | `/api/v1/attachments/`        | Upload, download, image processing |
| Auth          | `/api/v1/auth/`               | Login, register, OAuth2, OIDC, TOTP, API keys |
| GitHub        | `/api/v1/github/`             | Sync, status, configure |
| Admin         | `/api/v1/admin/`              | Stats, user management, audit logs |
| Research      | `/api/v1/research/`           | Research notes, AI analysis |
| SCIM          | `/scim/v2/Users/`             | User provisioning |
| GDPR          | `/gdpr/`                      | Data export, account deletion |
| Webhooks      | `/api/v1/webhooks/`           | Register, list, trigger |

---

## 🧪 Testing

```bash
python manage.py test apps
```

With coverage:

```bash
coverage run manage.py test apps
coverage report
```

---

## 📄 License

MIT – see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Pull requests are welcome! See the [main Memora repository](https://github.com/yourusername/memora) for guidelines.

---

## 🔗 Links

- **Memora (full project):** https://github.com/yourusername/memora
- **Gotion (Go backend):** https://github.com/yourusername/gotion
- **Documentation:** https://github.com/yourusername/memora/tree/main/docs
- **Issue tracker:** https://github.com/yourusername/memora/issues

---

**memora‑django** — the batteries‑included Django backend that scales with Gotion when you need raw Go performance.
``
