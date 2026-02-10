# Production Deployment Guide

This guide provides comprehensive instructions for deploying the **nbx-django** application to production on Railway.

## Table of Contents

- [Overview](#overview)
- [Environment Variables](#environment-variables)
- [Railway Deployment Setup](#railway-deployment-setup)
- [CI/CD Pipeline](#cicd-pipeline)
- [Production Services](#production-services)
- [Security Best Practices](#security-best-practices)
- [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)

---

## Overview

**nbx-django** is deployed to [Railway](https://railway.app/) using:
- **Platform**: Railway (PaaS)
- **Python Version**: 3.11.x (pinned via `.python-version` and `runtime.txt`)
- **Web Server**: Gunicorn
- **Database**: PostgreSQL (Railway-managed)
- **Static Files**: WhiteNoise
- **Email**: Mailgun via Django-Anymail
- **Background Jobs**: Django-Q worker
- **CI/CD**: GitHub Actions

### Architecture

```
GitHub (main branch)
    ↓
GitHub Actions (CI/CD)
    ↓ (tests pass)
Railway Deployment
    ├── Release Phase: python manage.py migrate
    └── Web Process: gunicorn nbxdjango.wsgi
    └── Worker Process: python manage.py qcluster
```

---

## Environment Variables

### Required Variables

These environment variables **must** be set in production:

| Variable | Description | Example | Where to Get |
|----------|-------------|---------|--------------|
| `SECRET_KEY` | Django secret key for cryptographic signing | `django-insecure-xyz...` | Generate with `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'` |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://user:pass@host:5432/db` | Auto-provided by Railway PostgreSQL service |
| `DEBUG` | Enable/disable debug mode | `False` | **Must be `False` in production** |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames | `app.railway.app,yourdomain.com` | Your Railway domain or custom domain |
| `MAILGUN_API_KEY` | Mailgun API key for sending emails | `key-abc123...` | [Mailgun Dashboard](https://app.mailgun.com/) |
| `MAILGUN_SENDER_DOMAIN` | Mailgun verified sender domain | `mg.yourdomain.com` | [Mailgun Domains](https://app.mailgun.com/domains) |

### Optional Variables with Defaults

These variables have sensible defaults but can be customized:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | `http://localhost:3000` | `https://app.yourdomain.com,https://admin.yourdomain.com` |
| `FRONTEND_URL` | Frontend application URL for password reset links | `http://localhost:3000` | `https://app.yourdomain.com` |
| `NARBOX_LOGO_URL` | Public URL for logo in email templates | *(empty)* | `https://yourdomain.com/static/logo.png` |
| `DJANGO_SETTINGS_MODULE` | Django settings module path | `nbxdjango.settings` | *Rarely needs to change* |

### Environment Variable Matrix

| Variable | Development | Production |
|----------|-------------|------------|
| `DEBUG` | `True` | `False` (required) |
| `SECRET_KEY` | Auto-generated or dummy | Strong random key (required) |
| `DATABASE_URL` | Local PostgreSQL | Railway PostgreSQL (auto) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Your domain(s) (required) |
| `MAILGUN_API_KEY` | Optional (for testing) | Required |
| `MAILGUN_SENDER_DOMAIN` | Optional (for testing) | Required |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Your frontend URL(s) |
| `FRONTEND_URL` | `http://localhost:3000` | Your frontend URL |

### Security Notes

⚠️ **Critical Security Requirements:**

1. **Never commit secrets to Git** - Use Railway environment variables UI
2. **Generate a strong SECRET_KEY** - Use the command provided above
3. **Set DEBUG=False** - Debug mode exposes sensitive information
4. **Restrict ALLOWED_HOSTS** - Only list your actual domains
5. **Use HTTPS only** - Railway provides HTTPS by default
6. **Protect API keys** - Mailgun keys should never be in code

---

## Railway Deployment Setup

### Prerequisites

- GitHub account with access to the repository
- Railway account ([Sign up](https://railway.app/))
- Mailgun account for email sending ([Sign up](https://signup.mailgun.com/))
- **Python 3.11.x** (required for Railway deployment - specified in `.python-version` and `runtime.txt`)

### Step 1: Create Railway Project

1. **Login to Railway**: Go to [railway.app](https://railway.app/) and sign in with GitHub
2. **Create New Project**: Click "New Project"
3. **Deploy from GitHub**: Select "Deploy from GitHub repo"
4. **Select Repository**: Choose your `nbx-django` repository
5. **Project Name**: Name it `nbx-django` or your preferred name

### Step 2: Add PostgreSQL Database

1. **In your Railway project**: Click "New" → "Database" → "Add PostgreSQL"
2. **Wait for provisioning**: Railway will automatically create the database
3. **DATABASE_URL**: Railway automatically sets this variable in your app

### Step 3: Configure Environment Variables

Navigate to your Railway service → **Variables** tab and add:

```bash
# Required
SECRET_KEY=<generate-using-command-above>
DEBUG=False
ALLOWED_HOSTS=<your-railway-domain>.railway.app
MAILGUN_API_KEY=<your-mailgun-key>
MAILGUN_SENDER_DOMAIN=<your-mailgun-domain>

# Optional (customize for your setup)
CORS_ALLOWED_ORIGINS=https://your-frontend.com
FRONTEND_URL=https://your-frontend.com
NARBOX_LOGO_URL=https://your-domain.com/static/logo.png
```

**To generate SECRET_KEY:**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Step 4: Configure Procfile

The project includes a `Procfile` that Railway uses automatically:

```procfile
release: python nbxdjango/manage.py migrate
web: cd nbxdjango && gunicorn nbxdjango.wsgi --log-file -
```

**What this does:**
- **release**: Runs database migrations before deployment goes live
- **web**: Starts Gunicorn web server to handle HTTP requests

### Step 5: Add Django-Q Worker (Background Jobs)

Django-Q requires a separate worker process for background email processing:

1. **In Railway project**: Click "New" → "Empty Service"
2. **Name it**: `nbx-django-worker`
3. **Link to same repo**: Connect the same GitHub repository
4. **Set variables**: Copy all environment variables from the web service
5. **Override start command**: In Settings → Deploy, set custom start command:
   ```bash
   cd nbxdjango && python manage.py qcluster
   ```

**Why a separate worker?**
- Handles async email sending without blocking web requests
- Can be scaled independently
- Prevents email delays from affecting user experience

### Step 6: Deploy

Railway automatically deploys when you push to your main branch via GitHub Actions (see CI/CD section below).

**Manual deploy:**
1. Go to Railway service → Deployments
2. Click "Deploy Now" to trigger manual deployment

### Step 7: Verify Deployment

1. **Check deployment logs**: Railway → Deployments → View logs
2. **Test the GraphQL endpoint**: `https://<your-domain>.railway.app/graphql`
3. **Test admin panel**: `https://<your-domain>.railway.app/admin`
4. **Verify HTTPS redirect**: Try HTTP, should redirect to HTTPS

---

## CI/CD Pipeline

The project uses **GitHub Actions** for automated testing and deployment.

### Workflow Overview

**File**: `.github/workflows/ci.yml`

```
Push/PR to main/master/develop
    ↓
Run Tests (with PostgreSQL)
    ├── Install dependencies
    ├── Run migrations
    ├── Execute pytest
    └── Upload coverage to Codecov
    ↓ (only on main branch)
Deploy to Railway
    └── Uses Railway CLI
```

### Required GitHub Secrets

Set these in your GitHub repository: **Settings** → **Secrets and variables** → **Actions**

| Secret | Description | How to Get |
|--------|-------------|------------|
| `RAILWAY_TOKEN` | Railway API token for deployments | Railway → Account Settings → Tokens → Create Token |
| `CODECOV_TOKEN` | (Optional) For coverage reports | [Codecov.io](https://codecov.io/) after linking repo |

**To create RAILWAY_TOKEN:**
1. Go to Railway dashboard
2. Click your profile (top right) → Account Settings
3. Navigate to "Tokens" section
4. Click "Create Token"
5. Copy token and add to GitHub secrets

### Deployment Triggers

| Branch | Action | Result |
|--------|--------|--------|
| `main` | Push or merge | ✅ Tests run → ✅ Deploys to production |
| `master` | Push or merge | ✅ Tests run → ❌ No deploy |
| `develop` | Pull request | ✅ Tests run → ❌ No deploy |
| Any other | - | ❌ No action |

### Branch Strategy

**Recommended workflow:**
1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and commit
3. Push and create PR to `develop`: Tests run automatically
4. Merge to `develop`: Tests run
5. Merge `develop` to `main`: Tests run + Deploy to Railway

### CI/CD Environment

Tests run with:
- **Python**: 3.11
- **PostgreSQL**: 16
- **Environment**:
  - `DEBUG=true`
  - `SECRET_KEY=test-secret-key-not-for-production`
  - `DATABASE_URL=postgres://postgres:postgres@localhost:5432/app_test`

---

## Production Services

### Web Service (Gunicorn)

**What it does**: Serves HTTP requests for Django application

**Configuration**:
- **Server**: Gunicorn (production-grade WSGI server)
- **Command**: `cd nbxdjango && gunicorn nbxdjango.wsgi --log-file -`
- **Logs to**: stdout (visible in Railway logs)

**Gunicorn features**:
- Multiple worker processes for concurrency
- Graceful worker restarts
- Request timeout handling
- Logging to Railway

### Worker Service (Django-Q)

**What it does**: Processes background tasks, primarily email sending

**Configuration**:
- **Command**: `cd nbxdjango && python manage.py qcluster`
- **Workers**: 4 (configured in settings.py)
- **Queue**: Uses PostgreSQL as queue backend

**Django-Q Settings** (`settings.py`):
```python
Q_CLUSTER = {
    "name": "DjangORM",
    "workers": 4,
    "timeout": 90,
    "retry": 120,
    "queue_limit": 50,
    "bulk": 10,
    "orm": "default",
}
```

**Why Django-Q?**
- Prevents slow email API calls from blocking user requests
- Automatic retry on failures
- Uses PostgreSQL (no Redis required)

### Database (PostgreSQL)

**Managed by**: Railway

**Configuration**:
- **Version**: PostgreSQL 16
- **Connection pooling**: 600 seconds (`conn_max_age=600`)
- **Health checks**: Enabled (`conn_health_checks=True`)

**Migrations**:
- Run automatically via `release` phase in Procfile
- Executes before new deployment goes live
- Zero-downtime deployments

**Backup recommendation**: 
- Use Railway's built-in backup feature
- Or set up pg_dump scheduled backups

### Email Service (Mailgun)

**Configuration**:
```python
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
ANYMAIL = {
    "MAILGUN_API_KEY": os.environ.get("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": os.environ.get("MAILGUN_SENDER_DOMAIN"),
}
```

**Setup steps**:
1. Create Mailgun account
2. Verify your sending domain
3. Get API key from dashboard
4. Add environment variables to Railway
5. Update `DEFAULT_FROM_EMAIL` in settings if needed

**Email features**:
- Async sending via Django-Q
- Automatic retry on failures
- HTML email templates

### Static Files (WhiteNoise)

**Configuration**:
```python
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

**How it works**:
1. `collectstatic` runs during build (if needed)
2. WhiteNoise serves static files directly from Gunicorn
3. Files are compressed (gzip/brotli)
4. Cache headers for optimal performance

**No CDN required**: WhiteNoise efficiently serves static files from your app

### CORS Configuration

**Settings**:
```python
CORS_ALLOW_ALL_ORIGINS = False  # ⚠️ Never set to True in production
CORS_ALLOWED_ORIGINS = [
    # From CORS_ALLOWED_ORIGINS env var
    "https://your-frontend.com",
]
CORS_ALLOW_CREDENTIALS = True
```

**Important**:
- Set `CORS_ALLOWED_ORIGINS` to your frontend domain(s)
- Comma-separated for multiple domains
- Must include protocol (https://)
- Never use `CORS_ALLOW_ALL_ORIGINS = True` in production

---

## Security Best Practices

### Production Security Checklist

Before deploying to production, verify:

- [ ] `DEBUG = False` in production
- [ ] Strong random `SECRET_KEY` generated and set
- [ ] `ALLOWED_HOSTS` contains only your actual domains
- [ ] `CORS_ALLOWED_ORIGINS` restricts to your frontend domain(s)
- [ ] `DATABASE_URL` uses SSL (Railway default)
- [ ] All sensitive env vars set in Railway (not in code)
- [ ] `.env` file is in `.gitignore`
- [ ] No secrets committed to Git history

### Django Security Settings (Production)

When `DEBUG=False`, these security settings are automatically enabled:

| Setting | Production Value | Purpose |
|---------|-----------------|---------|
| `SECURE_SSL_REDIRECT` | `True` | Redirects HTTP → HTTPS |
| `SECURE_HSTS_SECONDS` | `31536000` (1 year) | Enforce HTTPS in browsers |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `True` | Apply HSTS to subdomains |
| `SECURE_HSTS_PRELOAD` | `True` | Enable HSTS preload list |
| `SESSION_COOKIE_SECURE` | `True` | Cookies only over HTTPS |
| `CSRF_COOKIE_SECURE` | `True` | CSRF tokens only over HTTPS |
| `SESSION_COOKIE_HTTPONLY` | `True` | Prevents JavaScript cookie access |
| `CSRF_COOKIE_HTTPONLY` | `True` | Prevents JavaScript CSRF access |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `True` | Prevents MIME sniffing |
| `SECURE_BROWSER_XSS_FILTER` | `True` | XSS protection |
| `X_FRAME_OPTIONS` | `DENY` | Prevents clickjacking |

### SECRET_KEY Management

**Generate a strong key:**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

**Best practices:**
- Minimum 50 characters
- Random alphanumeric + special characters
- Never reuse across environments
- Never commit to version control
- Rotate periodically (requires re-signing sessions)

**What SECRET_KEY protects:**
- Session data
- CSRF tokens
- Password reset tokens
- Signed cookies

**If compromised**: 
1. Generate new key
2. Update in Railway
3. Users will need to log in again
4. Outstanding password reset links will expire

### ALLOWED_HOSTS Configuration

**Development**:
```python
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
```

**Production**:
```python
ALLOWED_HOSTS = ["your-app.railway.app", "yourdomain.com", "www.yourdomain.com"]
```

**Why it matters**:
- Protects against Host header attacks
- Django returns 400 Bad Request for invalid hosts
- Set via `ALLOWED_HOSTS` environment variable (comma-separated)

**Example**:
```bash
ALLOWED_HOSTS=app.railway.app,api.yourdomain.com,yourdomain.com
```

### Database Security

**Connection**:
- Railway provides SSL by default
- Connection pooling reduces connection overhead
- Health checks ensure connection validity

**Credentials**:
- `DATABASE_URL` is auto-generated by Railway
- Includes strong random password
- Only accessible within Railway private network

**Migrations**:
- Run in `release` phase (before deployment)
- Automatic and atomic
- Can be rolled back if needed

### Authentication & Authorization

**JWT Tokens**:
- 7-day refresh token expiration
- Middleware validates all GraphQL requests
- Email-based authentication via custom backend

**Password policies**:
- Minimum length validation
- Common password checking
- User attribute similarity check
- Numeric-only password prevention

---

## Monitoring and Troubleshooting

### Viewing Logs

**Railway dashboard**:
1. Navigate to your project
2. Select the service (web or worker)
3. Click "Deployments" → Select deployment → "View logs"

**Log types**:
- **Build logs**: Dependency installation, collectstatic
- **Deploy logs**: Release phase (migrations), app startup
- **Application logs**: Django/Gunicorn runtime logs

**Useful log filters**:
- `ERROR` - Application errors
- `WARNING` - Potential issues
- `INFO` - General information
- Gunicorn access logs show all HTTP requests

### Common Issues and Solutions

#### 1. Python Version Compatibility Error (pkg_resources)

**Symptom**: Deployment fails with `ModuleNotFoundError: No module named 'pkg_resources'` or `django_q` import errors

**Root Cause**: Railway is using Python 3.13, but `django-q` requires `pkg_resources` which has compatibility issues with Python 3.13.

**Solution**:
The project includes `.python-version` and `runtime.txt` files that pin Python to 3.11.x. Ensure these files exist:

```bash
# .python-version
3.11.10

# runtime.txt
python-3.11.10
```

Railway will automatically detect these files and use Python 3.11 instead of the latest version.

**Verification**:
1. Check deployment logs for `Using Python version 3.11.x`
2. Ensure the files are committed to the repository
3. Trigger a new deployment after adding these files

#### 2. Deployment Fails with "SECRET_KEY not set"

**Symptom**: Build fails, error mentions `SECRET_KEY`

**Solution**:
1. Generate key: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
2. Add to Railway variables: `SECRET_KEY=<generated-key>`
3. Redeploy

#### 3. Database Connection Errors

**Symptom**: `django.db.utils.OperationalError` or connection refused

**Solutions**:
- **Check DATABASE_URL**: Ensure PostgreSQL service is running in Railway
- **Verify connection**: Railway auto-links database, check Variables tab
- **Database not created**: Ensure PostgreSQL service exists in project
- **Connection timeout**: Check Railway status page for outages

**Verify database connection**:
```bash
# In Railway service shell (if available)
python nbxdjango/manage.py dbshell
```

#### 4. Static Files Not Loading (404 errors)

**Symptom**: CSS/JS/images return 404 errors

**Solutions**:
1. **Verify STATIC_ROOT**: Should be `BASE_DIR / "staticfiles"`
2. **Check WhiteNoise**: Must be in `MIDDLEWARE` (after `SecurityMiddleware`)
3. **Run collectstatic** (if not automatic):
   ```bash
   python nbxdjango/manage.py collectstatic --noinput
   ```
4. **Check STATIC_URL**: Should be `/static/`

**WhiteNoise should be configured as**:
```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # ← Must be here
    # ... other middleware
]
```

#### 5. ALLOWED_HOSTS Errors (Bad Request 400)

**Symptom**: Accessing site returns "Bad Request (400)"

**Solution**:
1. Check Railway-provided domain in project settings
2. Update `ALLOWED_HOSTS` environment variable:
   ```bash
   ALLOWED_HOSTS=your-app.railway.app
   ```
3. For custom domains, add them:
   ```bash
   ALLOWED_HOSTS=your-app.railway.app,yourdomain.com,www.yourdomain.com
   ```
4. Redeploy after updating

#### 6. Emails Not Sending

**Symptom**: No emails received, or errors in worker logs

**Solutions**:
1. **Check worker is running**: Verify `nbx-django-worker` service is deployed
2. **Verify Mailgun credentials**:
   - `MAILGUN_API_KEY` is correct (starts with `key-`)
   - `MAILGUN_SENDER_DOMAIN` matches verified domain in Mailgun
3. **Check Django-Q logs**:
   ```python
   # In Django shell
   from django_q.models import Task, Failure
   Task.objects.all()  # Recent tasks
   Failure.objects.all()  # Failed tasks
   ```
4. **Test email sending**:
   ```python
   from packagehandling.utils import send_email
   send_email("Test", "Test email body", ["test@example.com"])
   ```
5. **Check Mailgun dashboard**: Look for send attempts and errors

#### 7. Migration Errors During Deploy

**Symptom**: Release phase fails with migration errors

**Solutions**:
- **Conflicting migrations**: Resolve conflicts locally, commit, push
- **Missing dependency**: Ensure `requirements.txt` includes all packages
- **Database state issue**: 
  ```bash
  # In production shell (careful!)
  python nbxdjango/manage.py migrate --fake <app> <migration>
  ```
- **Rollback**: Deploy previous working commit

#### 8. CORS Errors from Frontend

**Symptom**: Browser console shows CORS errors, API requests fail

**Solution**:
1. **Add frontend origin** to `CORS_ALLOWED_ORIGINS`:
   ```bash
   CORS_ALLOWED_ORIGINS=https://your-frontend.com,https://app.yourdomain.com
   ```
2. **Include protocol**: Must use `https://` (not `http://` in production)
3. **Check for typos**: URL must match exactly
4. **Verify setting**: `CORS_ALLOW_CREDENTIALS = True` for authenticated requests
5. **Redeploy** after updating environment variables

#### 9. GraphQL Endpoint Returns 404

**Symptom**: Cannot access `/graphql`

**Solutions**:
- **Check DEBUG mode**: GraphiQL interface only available when `DEBUG=True`
- **Verify URL**: Should be `https://your-domain.railway.app/graphql`
- **Check URL configuration**: Ensure `urls.py` includes GraphQL route
- **Production note**: GraphQL endpoint works, but interactive UI is disabled

**To enable GraphiQL in production** (not recommended):
```python
# In nbxdjango/urls.py
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

urlpatterns = [
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True))),
    # ...
]
```

### Health Checks

**Railway automatic health checks**:
- Monitors service availability
- Restarts unhealthy instances
- No configuration needed

**Manual health check endpoint** (recommended to add):

Create `nbxdjango/packagehandling/views.py`:
```python
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "healthy", "database": "ok"})
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=503)
```

Add to `nbxdjango/nbxdjango/urls.py`:
```python
from packagehandling.views import health_check

urlpatterns = [
    path("health/", health_check),
    # ... existing paths
]
```

### Performance Monitoring

**Railway built-in metrics**:
- CPU usage
- Memory usage
- Request count
- Response times

**Access metrics**:
1. Railway project → Service
2. Click "Metrics" tab
3. View real-time and historical data

**Recommended external monitoring** (optional):
- [Sentry](https://sentry.io/) - Error tracking
- [New Relic](https://newrelic.com/) - APM
- [Datadog](https://www.datadoghq.com/) - Infrastructure monitoring

### Scaling

**Railway scaling options**:
1. **Vertical scaling**: Increase RAM/CPU in service settings
2. **Horizontal scaling**: Add replicas (paid plan)
3. **Worker scaling**: Deploy multiple worker services

**When to scale**:
- CPU consistently > 80%
- Memory consistently > 80%
- Response times increasing
- Background job queue backing up

---

## Quick Reference

### Essential Commands

```bash
# Generate SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Run migrations
python nbxdjango/manage.py migrate

# Create superuser (non-interactive)
DJANGO_SUPERUSER_USERNAME=admin \
DJANGO_SUPERUSER_EMAIL=admin@example.com \
DJANGO_SUPERUSER_PASSWORD=securepass \
python nbxdjango/manage.py create_superuser_script

# Collect static files
python nbxdjango/manage.py collectstatic --noinput

# Start web server locally
python nbxdjango/manage.py runserver

# Start worker locally
python nbxdjango/manage.py qcluster
```

### Environment Variables Quick Copy

```bash
# Required
SECRET_KEY=<generate-me>
DEBUG=False
DATABASE_URL=<auto-provided-by-railway>
ALLOWED_HOSTS=<your-railway-domain>.railway.app
MAILGUN_API_KEY=<your-mailgun-key>
MAILGUN_SENDER_DOMAIN=<your-mailgun-domain>

# Optional
CORS_ALLOWED_ORIGINS=https://your-frontend.com
FRONTEND_URL=https://your-frontend.com
NARBOX_LOGO_URL=
```

### Important Links

- **Railway Dashboard**: https://railway.app/dashboard
- **Mailgun Dashboard**: https://app.mailgun.com/
- **GitHub Actions**: https://github.com/YOUR_USERNAME/nbx-django/actions
- **Codecov** (optional): https://codecov.io/

---

## Support and Additional Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **Railway Documentation**: https://docs.railway.app/
- **Graphene-Django**: https://docs.graphene-python.org/projects/django/
- **Django-Q**: https://django-q.readthedocs.io/
- **WhiteNoise**: http://whitenoise.evans.io/

For project-specific questions, refer to:
- **README.md** - Local development setup
- **AGENTS.md** - AI agent development guide
- **GRAPHQL_API.md** - Complete API documentation
