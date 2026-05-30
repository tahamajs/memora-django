# 🐍 memora‑django

[![PyPI version](https://badge.fury.io/py/memora-django.svg)](https://badge.fury.io/py/memora-django)
[![Python Versions](https://img.shields.io/pypi/pyversions/memora-django.svg)](https://pypi.org/project/memora-django)
[![Django Versions](https://img.shields.io/badge/django-5.0%20%7C%204.2-blue.svg)](https://www.djangoproject.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/yourusername/memora/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/memora/actions)

**memora‑django** is a reusable Django backend for the **Memora** local‑first note‑taking platform. It provides a full REST API with AI integration, Git sync, and dozens of enterprise features out of the box.

Add it to any Django project and instantly get:

- ✅ Complete note management with Markdown & versioning
- 🤖 AI‑powered summarisation, tagging, and writing improvement
- 🔄 Automatic Git version control & GitHub sync
- 🔬 Research mode with methodology tracking
- 🔐 JWT, OAuth2, TOTP, and API key authentication
- 📎 File attachments with multiple storage backends
- 📊 Admin dashboard, Prometheus metrics, audit logging
- … and 60+ more modules

---

## 📦 Installation

```bash
pip install memora-django
```

Requires **Python 3.10+** and **Django 5.0+** (4.2 supported with limited features).

---

## 🚀 Quick Start

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

Create a `.env` file or export:

```bash
DJANGO_SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...
DATABASE_URL=sqlite:///db.sqlite3   # or PostgreSQL
```

The full list of configuration options is in the [Configuration](#-configuration) section.

---

## ⚙️ Configuration

All settings can be configured via environment variables or Django settings.

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

> All settings can also be placed in Django’s `settings.py` with the same names (uppercase).

---

## 📡 API Reference

When the server is running, interactive Swagger documentation is available at:

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

### Example: Create a note

```http
POST /api/v1/notes/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "My Note",
  "content": "# Hello\nThis is markdown.",
  "category_id": 1,
  "tag_ids": [1, 2]
}
```

### Example: AI summarization

```http
POST /api/v1/ai/summarize/
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Long text to summarize...",
  "style": "concise"
}
```

---

## 🧱 Architecture

```
┌─────────────────────────────┐
│          Your Django App     │
├─────────────────────────────┤
│          memora‑django       │
│  ┌─────────────────────────┐│
│  │        API Layer        ││
│  │  (REST + GraphQL + WS)  ││
│  ├─────────────────────────┤│
│  │     Service Layer       ││
│  │  (Notes, AI, Git, ...)  ││
│  ├─────────────────────────┤│
│  │       Data Layer        ││
│  │  (SQLite / PostgreSQL)  ││
│  └─────────────────────────┘│
└─────────────────────────────┘
```

---

## 🧪 Testing

Run the included test suite:

```bash
python manage.py test apps
```

To run tests with coverage:

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

- **Homepage:** https://github.com/yourusername/memora
- **Documentation:** https://github.com/yourusername/memora/tree/main/docs
- **Issue tracker:** https://github.com/yourusername/memora/issues

---

**memora‑django** — the fastest way to build a local‑first, AI‑powered note‑taking backend with Django.
