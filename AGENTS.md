# AGENTS.md - AI Coding Agent Guide

This file contains essential information for AI coding agents working on the nbx-django project.

## Project Overview

**nbx-django** is a Django-based package management system. It provides a GraphQL API for managing clients, packages, and consolidations. The project is designed for deployment on Railway with PostgreSQL as the primary database.

### Key Features
- **Client Management**: Track client information with contact details and addresses
- **Package Tracking**: Manage packages with barcode, courier info, dimensions, weight, and pricing
- **Consolidation**: Group packages into consolidations with status tracking
- **Asynchronous Email**: Django-Q + Mailgun for non-blocking email delivery
- **Authentication**: JWT-based authentication with email/password login

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend Framework** | Django 4.2 |
| **API** | GraphQL (Graphene-Django) |
| **Database** | PostgreSQL |
| **Authentication** | django-graphql-jwt |
| **Email** | Mailgun via django-anymail + Django-Q |
| **CORS** | django-cors-headers |
| **Static Files** | WhiteNoise |
| **WSGI Server** | Gunicorn |
| **Testing** | pytest, pytest-django, factory-boy |
| **Code Quality** | flake8, black, isort, mypy |
| **MCP Server** | mcp-django |

## MCP Server (mcp-django)

The project includes `mcp-django`, an MCP server that allows LLM clients to interact with the Django project through a stateful Python shell.

### Configuration Files
- `.vscode/mcp.json` - VS Code MCP configuration
- `mcp-config.json` - General MCP client configuration reference
- `MCP_SETUP.md` - Detailed setup instructions

### Available Resources
- `django://project` - Project information and configuration
- `django://apps` - List of installed apps and their models
- `django://models` - Detailed model information

### Available Tools
- `shell` - Execute Python code in a persistent Django environment
- `shell_reset` - Reset the shell session

### Running the MCP Server

**Direct execution:**
```bash
cd nbxdjango
python -m mcp_django
```

**Via Django management command:**
```bash
cd nbxdjango
python manage.py mcp
```

## Project Structure

```
nbx-django/
├── nbxdjango/                     # Main Django project
│   ├── nbxdjango/                 # Project configuration
│   │   ├── settings.py            # Django settings
│   │   ├── urls.py                # URL routing
│   │   ├── wsgi.py                # WSGI entry point
│   │   └── asgi.py                # ASGI entry point
│   ├── packagehandling/           # Main Django app
│   │   ├── models/                # Data models
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # Client model
│   │   │   ├── package.py         # Package model
│   │   │   ├── consolidate.py     # Consolidation model
│   │   │   └── user.py            # CustomUser model
│   │   ├── schema/                # GraphQL schema
│   │   │   ├── types.py           # GraphQL types
│   │   │   ├── queries.py         # Query aggregations
│   │   │   ├── mutations.py       # Mutation aggregations
│   │   │   ├── query_parts/       # Individual query modules
│   │   │   └── mutation_parts/    # Individual mutation modules
│   │   ├── tests/                 # Test suite
│   │   │   ├── models/            # Model tests
│   │   │   ├── queries/           # Query tests
│   │   │   └── mutations/         # Mutation tests
│   │   ├── management/commands/   # Custom management commands
│   │   ├── factories.py           # Test data factories (factory-boy)
│   │   ├── utils.py               # Utility functions (email)
│   │   ├── authentication.py      # Custom auth backend
│   │   ├── admin.py               # Django admin config
│   │   ├── apps.py                # App configuration
│   │   └── signals.py             # Django signals
│   └── manage.py                  # Django management script
├── .github/workflows/             # GitHub Actions
│   ├── ci.yml                     # CI/CD pipeline
│   └── lint.yml                   # Lint checks
├── documents/                     # Documentation
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
├── pyproject.toml                 # Tool configurations
├── Procfile                       # Railway deployment config
├── docker-compose.yml             # Local PostgreSQL setup
└── .env.example                   # Environment template
```

## Development Environment Setup

### Prerequisites
- Python 3.11
- PostgreSQL (or use Docker via docker-compose)

### Setup Steps

1. **Install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Start PostgreSQL (using Docker):**
   ```bash
   docker-compose up -d
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run migrations:**
   ```bash
   python nbxdjango/manage.py migrate
   ```

5. **Start the development server:**
   ```bash
   python nbxdjango/manage.py runserver
   ```

6. **Start the email worker (separate terminal):**
   ```bash
   python nbxdjango/manage.py qcluster
   ```

The GraphQL endpoint is available at `http://127.0.0.1:8000/graphql` (GraphiQL enabled in DEBUG mode).

## Build and Test Commands

### Running Tests
```bash
DJANGO_SETTINGS_MODULE=nbxdjango.settings DATABASE_URL=postgres://myuser:mypassword@localhost:5432/mydatabase pytest nbxdjango/packagehandling/tests/
```

With coverage:
```bash
cd nbxdjango && pytest --cov=. --cov-report=xml
```

### Code Quality Commands

**Check style issues:**
```bash
flake8 .
```

**Auto-format code:**
```bash
black .
```

**Organize imports:**
```bash
isort .
```

**Type checking:**
```bash
mypy .
```

**Run all pre-commit hooks:**
```bash
pre-commit run --all-files
```

## Code Style Guidelines

### Python/Django Conventions
- **Line length**: 120 characters (configured in `pyproject.toml` and `.flake8`)
- **Python version**: 3.11+
- **Import organization**: Use `isort` with black profile
- **Type hints**: Use mypy for type checking

### Naming Conventions

| Component | Convention | Example |
|-----------|------------|---------|
| Django Model | Singular, PascalCase | `Package`, `CustomUser` |
| GraphQL Type | `Type` suffix | `PackageType`, `ClientType` |
| Query Resolver | `resolve_` prefix | `resolve_all_packages` |
| Mutation Class | Action verb prefix | `CreatePackage`, `UpdateClient` |

### GraphQL Best Practices
1. **N+1 Prevention**: Always use `select_related()` or `prefetch_related()` in resolvers
2. **Data Writes**: Implement all write logic in Graphene Mutation classes, never in Query resolvers
3. **Type Definitions**: Explicitly list fields in `Meta.fields` rather than using `"__all__"` for security

### Exclusions (from flake8)
- `.git`, `__pycache__`, `venv`
- `*/migrations/*` (auto-generated migration files)
- `*/__init__.py`
- `tests.py`

## Testing Instructions

### Test Structure
- Model tests: `nbxdjango/packagehandling/tests/models/`
- Query tests: `nbxdjango/packagehandling/tests/queries/`
- Mutation tests: `nbxdjango/packagehandling/tests/mutations/`

### Writing Tests
- Use `pytest` and `pytest-django`
- Use `factory-boy` factories from `factories.py` for test data
- Use `@pytest.mark.django_db` for database tests
- Include full GraphQL queries/mutations in API tests

### Test Data Generation
Create fake data for manual testing:

**Create clients with associated users:**
```bash
python nbxdjango/manage.py create_fake_clients --count 10
```

**Create standalone users:**
```bash
python nbxdjango/manage.py create_fake_users --count 5 --password testpass123
```

**Create packages for specific clients:**
```bash
# For a specific client by ID
python nbxdjango/manage.py create_fake_packages --count 50 --client-id 1

# For a specific client by email
python nbxdjango/manage.py create_fake_packages --count 20 --client-email "user@example.com"

# With random consolidation assignment
python nbxdjango/manage.py create_fake_packages --count 30 --client-id 1 --with-consolidation
```

**Create consolidations with packages:**
```bash
# Create consolidations with packages for a specific client
python nbxdjango/manage.py create_fake_consolidations --count 3 --client-id 1 --packages 5
```

See README.md for complete documentation on all fake data commands.

### Creating a Superuser (Non-Interactive)
```bash
DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=admin@example.com DJANGO_SUPERUSER_PASSWORD=securepass python nbxdjango/manage.py create_superuser_script
```

## Security Considerations

### Environment Variables (Required)
| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key (keep secure) |
| `DATABASE_URL` | PostgreSQL connection string |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `DEBUG` | Set to `False` in production |
| `MAILGUN_API_KEY` | Mailgun API key |
| `MAILGUN_SENDER_DOMAIN` | Mailgun sender domain |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins |

### Authentication
- JWT tokens with 7-day refresh expiration
- Custom email-based authentication backend
- Password reset via email

### CORS
- `CORS_ALLOW_ALL_ORIGINS = False` in production
- Configure allowed origins via `CORS_ALLOWED_ORIGINS` env var

## Deployment

### Platform: Railway
The project is configured for Railway deployment via GitHub Actions.

### CI/CD Pipeline
1. **Triggers**: Push/merge to `main` or PR to `master`/`develop`
2. **Test Job**: Runs migrations and pytest with PostgreSQL service
3. **Deploy Job**: Deploys to Railway if tests pass (main branch only)
4. **Release Phase**: Runs `migrate` before starting web process

### Production Configuration
- Static files served via WhiteNoise with compression
- Gunicorn as WSGI server
- Database connection pooling enabled
- Email queued via Django-Q

### Procfile Commands
```
release: python nbxdjango/manage.py migrate
web: cd nbxdjango && gunicorn nbxdjango.wsgi --log-file -
```

## Key Models

### CustomUser
- Email-based authentication (username optional)
- One-to-one relationship with Client

### Client
- Personal/contact information
- Address fields (state, city, streets, building)
- Related to User and has many Packages

### Package
- Barcode (unique), courier info
- Dimensions and weight with units
- Pricing (real and service prices)
- Optional consolidation grouping
- Belongs to one Client

### Consolidate
- Groups multiple packages
- Status workflow: pending → processing → in_transit → delivered
- Has delivery date and comments
- Belongs to one Client

## GraphQL Schema Entry Points

- **Schema definition**: `packagehandling/graphql_schema.py`
- **Queries**: `packagehandling/schema/queries.py`
- **Mutations**: `packagehandling/schema/mutations.py`
- **Types**: `packagehandling/schema/types.py`

### GraphQL API Documentation

See [GRAPHQL_API.md](./GRAPHQL_API.md) for complete documentation including:
- All queries and mutations with examples
- User permission matrices
- Error handling reference
- Common workflow examples
- Type definitions and field descriptions

## Additional Notes

- **Django Admin**: Available at `/admin/` with Package registered
- **Signals**: Defined in `packagehandling/signals.py`
- **Custom Commands**: Located in `packagehandling/management/commands/`
- **Email System**: Uses Django-Q for async processing via `send_email()` utility
