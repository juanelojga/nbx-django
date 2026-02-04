# Code Review Analysis - nbx-django

**Review Date:** 2026-02-03  
**Project:** nbx-django - Django-based package management system with GraphQL API  
**Scope:** Full codebase review covering security, performance, code quality, and best practices

---

## Executive Summary

This document provides a comprehensive analysis of the nbx-django codebase, identifying critical security vulnerabilities, performance bottlenecks, and areas for code quality improvement. Issues are categorized by severity and organized into actionable phases for implementation.

| Category | Count | Priority |
|----------|-------|----------|
| Security | 4 | Critical |
| Bugs | 5 | High |
| Code Quality | 6 | Medium |
| Testing | 3 | Medium |
| Best Practices | 6 | Low |

---

## Phase 1: Critical Security Issues

These issues pose immediate security risks and should be addressed first.

### 1.1 Missing Permission Checks in Consolidate Queries

**File:** `nbxdjango/packagehandling/schema/query_parts/consolidate_queries.py`

**Problem:** The `all_consolidates` and `consolidate_by_id` queries return all consolidations without any permission checks. Regular users can view other clients' consolidation data.

**Current Code:**
```python
class ConsolidateQueries(graphene.ObjectType):
    all_consolidates = graphene.List(ConsolidateType)
    consolidate_by_id = graphene.Field(ConsolidateType, id=graphene.ID())

    def resolve_all_consolidates(self, info):
        return Consolidate.objects.select_related("client").prefetch_related("packages").all()

    def resolve_consolidate_by_id(self, info, id):
        try:
            return Consolidate.objects.select_related("client").prefetch_related("packages").get(pk=id)
        except Consolidate.DoesNotExist:
            return None
```

**Recommended Fix:**
```python
from django.core.exceptions import PermissionDenied

class ConsolidateQueries(graphene.ObjectType):
    all_consolidates = graphene.List(ConsolidateType)
    consolidate_by_id = graphene.Field(ConsolidateType, id=graphene.ID())

    def resolve_all_consolidates(self, info):
        user = info.context.user
        if user.is_superuser:
            return Consolidate.objects.select_related("client").prefetch_related("packages").all()
        if hasattr(user, "client"):
            return Consolidate.objects.select_related("client").prefetch_related("packages").filter(client=user.client)
        raise PermissionDenied("You do not have permission to view this resource.")

    def resolve_consolidate_by_id(self, info, id):
        user = info.context.user
        try:
            consolidate = Consolidate.objects.select_related("client").prefetch_related("packages").get(pk=id)
        except Consolidate.DoesNotExist:
            return None
        
        if user.is_superuser:
            return consolidate
        if hasattr(user, "client") and consolidate.client == user.client:
            return consolidate
        raise PermissionDenied("You do not have permission to view this resource.")
```

**Impact:** High - Data exposure vulnerability

---

### 1.2 Hardcoded Password Reset URL

**File:** `nbxdjango/packagehandling/schema/mutation_parts/auth_mutations.py:67`

**Problem:** The password reset URL is hardcoded to `localhost:3000`, which won't work in production environments.

**Current Code:**
```python
reset_url = f"http://localhost:3000/reset-password?uid={uidb64}&token={token}"
```

**Recommended Fix:**

1. Add to `settings.py`:
```python
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
```

2. Update the mutation:
```python
from django.conf import settings

reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uidb64}&token={token}"
```

3. Add to `.env.example`:
```
FRONTEND_URL=http://localhost:3000
```

**Impact:** High - Password reset non-functional in production

---

### 1.3 UserType Exposes Sensitive Fields

**File:** `nbxdjango/packagehandling/schema/types.py:8-11`

**Problem:** The `UserType` exposes all user fields including `password` (hashed), `is_superuser`, and permission-related fields.

**Current Code:**
```python
class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = "__all__"
```

**Recommended Fix:**
```python
class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "username", "first_name", "last_name", "is_active", "date_joined")
        # Explicitly exclude: password, is_superuser, is_staff, groups, user_permissions
```

**Impact:** Medium - Information disclosure

---

### 1.4 No API Rate Limiting

**Problem:** The API lacks rate limiting on sensitive endpoints like `forgot_password`, `email_auth`, and token mutations, making it vulnerable to brute force and enumeration attacks.

**Recommended Fix:**

1. Install django-ratelimit:
```bash
pip install django-ratelimit
```

2. Add to `settings.py`:
```python
INSTALLED_APPS = [
    # ... existing apps
    "django_ratelimit",
]

# Optional: Configure cache for rate limiting
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
```

3. Apply to mutations (example for auth):
```python
from django_ratelimit.decorators import ratelimit
from graphql_jwt.decorators import login_required

class ForgotPassword(graphene.Mutation):
    # ... existing code
    
    @ratelimit(key="ip", rate="5/m", method="POST")
    def mutate(self, info, email):
        # ... existing logic
        pass
```

**Note:** For GraphQL specifically, you may need to implement rate limiting at the view level or use a custom decorator.

**Impact:** Medium - Brute force vulnerability

---

## Phase 2: High Priority Bugs

### 2.1 N+1 Query Problem in Package Queries

**File:** `nbxdjango/packagehandling/schema/query_parts/package_queries.py:28`

**Problem:** The `resolve_all_packages` method doesn't use `select_related` for the client and consolidate relationships, causing N+1 database queries.

**Current Code:**
```python
queryset = Package.objects.all()
```

**Recommended Fix:**
```python
queryset = Package.objects.select_related("client", "consolidate")
```

---

### 2.2 Missing select_related in resolve_client

**File:** `nbxdjango/packagehandling/schema/query_parts/client_queries.py:67-73`

**Problem:** Multiple database queries when checking permissions and fetching the client.

**Current Code:**
```python
def resolve_client(root, info, id):
    user = info.context.user
    if user.is_superuser:
        return Client.objects.get(pk=id)
    if not hasattr(user, "client") or user.client.id != id:
        raise PermissionDenied()
    return Client.objects.get(pk=id)
```

**Recommended Fix:**
```python
def resolve_client(root, info, id):
    user = info.context.user
    if user.is_superuser:
        return Client.objects.get(pk=id)
    
    # Use select_related to fetch user and client in one query
    client = Client.objects.filter(pk=id).select_related("user").first()
    if not client:
        raise PermissionDenied()
    if client.user != user:
        raise PermissionDenied()
    return client
```

---

### 2.3 Package Model clean() Method Not Called

**File:** `nbxdjango/packagehandling/models/package.py:34-36`

**Problem:** The `clean()` method validates that package and consolidate belong to the same client, but `clean()` is not automatically called by Django when using `Model.objects.create()` or `model.save()` in GraphQL mutations.

**Current Code:**
```python
def clean(self):
    if self.consolidate and self.client != self.consolidate.client:
        raise ValidationError("Package and Consolidate must belong to the same client.")
```

**Recommended Fix:**

Override `save()` method to ensure validation:
```python
def save(self, *args, **kwargs):
    self.clean()  # Call clean explicitly
    super().save(*args, **kwargs)
```

Also, ensure mutations call `full_clean()`:
```python
# In consolidate_mutations.py when adding packages
package.clean()
package.save()
```

---

### 2.4 Hardcoded print() Instead of Proper Logging

**File:** `nbxdjango/packagehandling/schema/mutation_parts/consolidate_mutations.py:81`

**Current Code:**
```python
print(f"Failed to send email for consolidate creation: {e}")
```

**Recommended Fix:**
```python
import logging

logger = logging.getLogger(__name__)

# In the mutation:
logger.error(f"Failed to send email for consolidate creation: {e}", exc_info=True)
```

Also add logging configuration to `settings.py`:
```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
```

---

### 2.5 Client Deletion Cascades to User Without Warning

**File:** `nbxdjango/packagehandling/schema/mutation_parts/client_mutations.py:93`

**Problem:** When a client is deleted, the associated user is also deleted (CASCADE), but there's no warning or check. This could accidentally delete user accounts.

**Current Code:**
```python
def mutate(self, info, id):
    user = info.context.user
    if not user.is_superuser:
        raise PermissionDenied()

    client = Client.objects.get(pk=id)
    client.delete()  # Also deletes associated user

    return DeleteClient(ok=True)
```

**Recommended Fix:**

Option 1 - Add explicit user deletion with confirmation:
```python
class DeleteClient(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        delete_user = graphene.Boolean(default_value=False)  # Explicit flag

    ok = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id, delete_user=False):
        user = info.context.user
        if not user.is_superuser:
            raise PermissionDenied()

        client = Client.objects.select_related("user").get(pk=id)
        
        if delete_user and client.user:
            client.user.delete()  # Client will be cascade-deleted
            message = "Client and associated user deleted successfully."
        else:
            # Option: Set user to inactive or unlink
            if client.user:
                client.user.is_active = False
                client.user.save()
            client.delete()
            message = "Client deleted. User account preserved but deactivated."

        return DeleteClient(ok=True, message=message)
```

Option 2 - Change relationship to SET_NULL:
```python
# In models/client.py
user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,  # Changed from CASCADE
    related_name="client",
    null=True,
    blank=True,
)
```

---

## Phase 3: Medium Priority Code Quality Issues

### 3.1 Email Uniqueness Not Enforced on Client Model

**File:** `nbxdjango/packagehandling/models/client.py:15`

**Current Code:**
```python
email = models.EmailField()
```

**Recommended Fix:**
```python
email = models.EmailField(unique=True)
```

Note: This requires a database migration and may fail if duplicate emails exist. Clean data before applying.

---

### 3.2 Inconsistent Error Handling

**Problem:** Mutations use different exception types inconsistently:
- `GraphQLError` (from graphql)
- `ValidationError` (from django)
- `PermissionDenied` (from django)

**Recommendation:** Standardize on:
- `ValidationError` for input validation errors
- `PermissionDenied` for authorization failures
- Create a custom exception handler if needed for consistent error formatting

---

### 3.3 Missing Type Hints

**Problem:** While mypy is configured, most functions lack type annotations.

**Recommendation:** Add type hints to all resolver and mutation methods:

```python
from typing import Optional
import graphene

def resolve_all_packages(
    root: None,
    info: graphene.ResolveInfo,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    order_by: Optional[str] = None,
    client_id: Optional[int] = None,
    not_in_consolidate: bool = True,
) -> PackageConnection:
    ...
```

---

### 3.4 Missing Database Indexes

**Files:** `models/client.py`, `models/package.py`, `models/consolidate.py`

**Problem:** Fields frequently used in filtering and ordering lack database indexes.

**Recommended Indexes:**

```python
# models/package.py
class Package(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["barcode"]),
            models.Index(fields=["client", "-created_at"]),
            models.Index(fields=["consolidate"]),
            models.Index(fields=["arrival_date"]),
        ]

# models/client.py
class Client(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["identification_number"]),
            models.Index(fields=["created_at"]),
        ]

# models/consolidate.py
class Consolidate(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["client", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["delivery_date"]),
        ]
```

---

### 3.5 Inconsistent PackageType Fields

**File:** `nbxdjango/packagehandling/schema/types.py:14-37`

**Problem:** The `PackageType` excludes `updated_at` but includes `created_at`.

**Current Code:**
```python
class PackageType(DjangoObjectType):
    class Meta:
        model = Package
        fields = (
            "id",
            "barcode",
            # ... other fields
            "created_at",
            # "updated_at" is missing
        )
```

**Recommended Fix:**
```python
class PackageType(DjangoObjectType):
    class Meta:
        model = Package
        fields = (
            "id",
            "barcode",
            "courier",
            "other_courier",
            "length",
            "width",
            "height",
            "dimension_unit",
            "weight",
            "weight_unit",
            "description",
            "purchase_link",
            "real_price",
            "service_price",
            "arrival_date",
            "created_at",
            "updated_at",  # Add this
            "client",
            "comments",
        )
```

---

### 3.6 Unused Imports

**Files:** Multiple files

**Examples:**
- `models/package.py:1` - `ValidationError` imported but not used at module level
- Various files have unused imports from copy-paste

**Recommendation:** Run `flake8` or `autoflake` to clean up unused imports:
```bash
flake8 --select=F401 nbxdjango/
```

---

## Phase 4: Testing Improvements

### 4.1 Missing Test Coverage

**Untested Components:**
- `schema/query_parts/consolidate_queries.py` - No tests exist
- `DeleteUser` mutation - No tests exist
- Token mutations (`TokenMutations` class) - No tests exist
- Email sending functionality - Mocked but not verified

**Recommended Test Structure:**
```
tests/
├── conftest.py                    # Shared fixtures
├── models/
│   └── test_consolidate.py        # Missing
├── queries/
│   └── test_consolidate_queries.py # Missing
└── mutations/
    ├── test_consolidate_mutations.py # Needs expansion
    ├── test_auth_mutations.py     # Missing - forgot/reset password
    └── test_user_mutations.py     # Missing - DeleteUser
```

---

### 4.2 Fixture Duplication

**Problem:** The `info_with_user_factory` fixture is defined in multiple test files.

**Files Affected:**
- `tests/mutations/test_package_mutations.py`
- Potentially others

**Recommended Fix:**

Create `nbxdjango/packagehandling/tests/conftest.py`:
```python
import pytest
from django.test import RequestFactory
from graphql.type import GraphQLResolveInfo as ResolveInfo


@pytest.fixture
def info_with_user_factory():
    def factory(user):
        request_factory = RequestFactory()
        request = request_factory.get("/graphql/")
        request.user = user
        return ResolveInfo(
            field_name="",
            field_nodes=[],
            return_type=None,
            parent_type=None,
            path=None,
            schema=None,
            fragments=None,
            root_value=None,
            operation=None,
            variable_values=None,
            context=request,
            is_awaitable=lambda: False,
        )
    return factory
```

Then remove duplicate fixtures from individual test files.

---

### 4.3 Missing Model Tests for Consolidate

**File to Create:** `nbxdjango/packagehandling/tests/models/test_consolidate.py`

**Recommended Tests:**
```python
import pytest
from packagehandling.factories import ClientFactory, ConsolidateFactory, PackageFactory
from packagehandling.models import Consolidate


@pytest.mark.django_db
class TestConsolidateModel:
    def test_create_consolidate(self):
        client = ClientFactory()
        consolidate = ConsolidateFactory(client=client)
        assert consolidate.id is not None
        assert consolidate.client == client

    def test_status_choices(self):
        assert Consolidate.Status.PENDING == "pending"
        assert Consolidate.Status.PROCESSING == "processing"
        # ... test all statuses

    def test_str_representation(self):
        client = ClientFactory()
        consolidate = ConsolidateFactory(client=client)
        assert str(consolidate) == f"Consolidate {consolidate.id} for {client}"
```

---

## Phase 5: Best Practices and Configuration

### 5.1 Missing Security Headers

**File:** `nbxdjango/nbxdjango/settings.py`

**Problem:** No security headers are configured for production.

**Recommended Configuration:**
```python
# Security settings for production
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Cookie security
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
```

**Note:** These require HTTPS in production.

---

### 5.2 Admin Configuration Incomplete

**File:** `nbxdjango/packagehandling/admin.py`

**Current Code:**
```python
from django.contrib import admin
from .models import Package

admin.site.register(Package)
```

**Recommended Fix:**
```python
from django.contrib import admin
from .models import Client, Consolidate, CustomUser, Package


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("barcode", "courier", "client", "created_at")
    list_filter = ("courier", "created_at")
    search_fields = ("barcode", "description", "client__email")
    raw_id_fields = ("client", "consolidate")


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "city", "created_at")
    search_fields = ("first_name", "last_name", "email", "identification_number")
    list_filter = ("state", "city", "created_at")


@admin.register(Consolidate)
class ConsolidateAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "status", "delivery_date", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("client__email", "description")
    filter_horizontal = ("packages",)  # If ManyToMany


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "is_superuser", "is_active", "date_joined")
    search_fields = ("email", "username")
    list_filter = ("is_superuser", "is_active", "date_joined")
```

---

### 5.3 Secret Key Configuration

**File:** `nbxdjango/nbxdjango/settings.py:27`

**Current Code:**
```python
SECRET_KEY = os.getenv("SECRET_KEY", "dummy-ci-secret-key")
```

**Problem:** While this is fine for CI, there's no validation that a real secret key is used in production.

**Recommended Fix:**
```python
import os
import sys

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    if "test" in sys.argv or "pytest" in sys.argv:
        SECRET_KEY = "dummy-ci-secret-key"
    elif not DEBUG:
        raise ValueError("SECRET_KEY environment variable must be set in production")
    else:
        SECRET_KEY = "dev-secret-key-not-for-production"
```

---

### 5.4 JSONField Without Validation

**File:** `nbxdjango/packagehandling/models/consolidate.py:24`

**Problem:** The `extra_attributes` JSON field accepts any JSON without schema validation.

**Recommendation:** Consider using Django's JSONSchemaValidator or a library like `jsonschema` if the structure should be validated:

```python
from django.core.validators import JSONSchemaValidator

CONSOLIDATE_EXTRA_SCHEMA = {
    "type": "object",
    "properties": {
        "tracking_number": {"type": "string"},
        "carrier": {"type": "string"},
    },
}

class Consolidate(models.Model):
    extra_attributes = models.JSONField(
        default=dict,
        validators=[JSONSchemaValidator(CONSOLIDATE_EXTRA_SCHEMA)],
    )
```

---

### 5.5 CORS Configuration Review

**File:** `nbxdjango/nbxdjango/settings.py:182-184`

**Current Code:**
```python
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
CORS_ALLOW_CREDENTIALS = True
```

**Recommendation:** Document the expected format for `CORS_ALLOWED_ORIGINS`:

```python
# .env.example
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://app.example.com

# settings.py - add comment
# Comma-separated list of allowed origins, e.g., "http://localhost:3000,https://app.example.com"
CORS_ALLOWED_ORIGINS = [
    origin.strip() 
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
```

---

### 5.6 Dependency Organization

**File:** `requirements.txt`

**Current Issue:** Development tools (flake8, black, mypy) are in the main requirements.

**Recommendation:** Move development dependencies to `requirements-dev.txt`:

```txt
# requirements.txt (production only)
Django==4.2
psycopg[binary]>=3.1.0
django-anymail[mailgun]
python-dotenv
django-q
django-cors-headers
graphene-django
django-graphql-jwt
gunicorn
dj-database-url
whitenoise
setuptools
mcp-django
```

```txt
# requirements-dev.txt (add these)
flake8==7.*
black==24.*
isort==5.*
mypy==1.*
pre-commit==3.*
pytest-django
factory-boy
pytest-cov
```

---

## Implementation Checklist

### Critical (Do First)
- [ ] Fix consolidate queries permission checks
- [ ] Make password reset URL configurable via environment
- [ ] Restrict UserType exposed fields
- [ ] Implement API rate limiting

### High Priority
- [ ] Add select_related to package queries
- [ ] Fix N+1 in client queries
- [ ] Ensure Package.clean() is called in mutations
- [ ] Replace print() with proper logging
- [ ] Review client/user deletion behavior

### Medium Priority
- [ ] Add unique constraint to Client.email
- [ ] Standardize error handling
- [ ] Add type hints
- [ ] Create database indexes
- [ ] Add missing updated_at field to PackageType
- [ ] Clean up unused imports

### Testing
- [ ] Create shared conftest.py with fixtures
- [ ] Add tests for consolidate queries
- [ ] Add tests for consolidate mutations
- [ ] Add tests for auth mutations (forgot/reset password)
- [ ] Add tests for DeleteUser mutation
- [ ] Add model tests for Consolidate

### Configuration & Best Practices
- [ ] Add security headers settings
- [ ] Register all models in admin.py
- [ ] Add production SECRET_KEY validation
- [ ] Organize requirements.txt vs requirements-dev.txt
- [ ] Document CORS_ALLOWED_ORIGINS format

---

## Appendix: Code Patterns to Follow

### GraphQL Permission Pattern
```python
def resolve_resource(root, info, id):
    user = info.context.user
    
    # Superuser can access everything
    if user.is_superuser:
        return Resource.objects.get(pk=id)
    
    # Regular users can only access their own resources
    if hasattr(user, "client"):
        return Resource.objects.get(pk=id, client=user.client)
    
    raise PermissionDenied("You do not have permission to view this resource.")
```

### Mutation Validation Pattern
```python
class CreateResource(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
    
    resource = graphene.Field(ResourceType)
    
    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        
        # Permission check
        if not user.is_superuser:
            raise PermissionDenied()
        
        # Input validation
        name = kwargs.get("name")
        if len(name) < 3:
            raise ValidationError("Name must be at least 3 characters.")
        
        # Business logic validation
        if Resource.objects.filter(name=name).exists():
            raise ValidationError("Resource with this name already exists.")
        
        resource = Resource.objects.create(**kwargs)
        return CreateResource(resource=resource)
```

### Query Optimization Pattern
```python
def resolve_all_resources(root, info, page=1, page_size=10):
    # Use select_related for ForeignKeys, prefetch_related for ManyToMany
    queryset = Resource.objects.select_related("client", "other_fk").prefetch_related("related_many")
    
    # Pagination
    total_count = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    items = queryset[start:end]
    
    return ResourceConnection(
        results=items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_next=end < total_count,
        has_previous=start > 0,
    )
```

---

*Document Version: 1.0*  
*Generated for nbx-django codebase review*
