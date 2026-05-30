backend-django/
├── manage.py
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── pytest.ini
├── setup.cfg
├── Makefile
├── notion_clone/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
├── apps/
│   ├── __init__.py
│   ├── notes/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── filters.py
│   │   ├── permissions.py
│   │   ├── services.py
│   │   ├── tasks.py
│   │   ├── signals.py
│   │   ├── admin.py
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py
│   │   │   ├── test_views.py
│   │   │   └── test_services.py
│   │   └── migrations/
│   │       └── __init__.py
│   ├── ai_service/
│   │   ├── __init__.py
│   │   ├── services.py
│   │   ├── prompts.py
│   │   └── views.py
│   ├── git_service/
│   │   ├── __init__.py
│   │   └── services.py
│   └── users/
│       ├── __init__.py
│       ├── models.py
│       ├── views.py
│       ├── serializers.py
│       └── urls.py
├── core/
│   ├── __init__.py
│   ├── middleware.py
│   ├── mixins.py
│   ├── pagination.py
│   ├── exceptions.py
│   └── utils.py
├── static/
│   └── .gitkeep
├── media/
│   └── .gitkeep
└── templates/
    ├── admin/
    │   └── base_site.html
    ├── emails/
    │   ├── welcome.html
    │   └── password_reset.html
    └── base.html