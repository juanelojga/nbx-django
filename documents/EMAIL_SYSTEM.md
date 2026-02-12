# Email System Documentation

## Overview

The nbx-django project uses an asynchronous email system powered by **Mailgun** (via `django-anymail`) and **Django-Q2** for background processing. This ensures email sending doesn't block GraphQL API responses.

---

## Architecture

```
GraphQL Mutation → send_email() → Django-Q2 Queue → Q Cluster Worker → Mailgun API
```

| Component | Technology | Purpose |
|-----------|------------|---------|
| Email Backend | `django-anymail` | Abstracts email provider (Mailgun) |
| Queue System | `django-q2` | Asynchronous task processing |
| Email Provider | Mailgun | Actual email delivery service |

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MAILGUN_API_KEY` | Yes | Your Mailgun API key |
| `MAILGUN_SENDER_DOMAIN` | Yes | Verified domain in Mailgun (e.g., `mg.yourdomain.com`) |

### Settings

Located in `nbxdjango/nbxdjango/settings.py`:

```python
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

ANYMAIL = {
    "MAILGUN_API_KEY": os.environ.get("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": os.environ.get("MAILGUN_SENDER_DOMAIN"),
}

DEFAULT_FROM_EMAIL = "noreply@yourdomain.com"
```

### Django-Q2 Configuration

```python
Q_CLUSTER = {
    "name": "DjangORM",
    "workers": 4,
    "timeout": 90,
    "retry": 120,
    "queue_limit": 50,
    "bulk": 10,
    "orm": "default",  # Uses Django ORM as the task broker
}
```

---

## Usage

### Starting the Email Worker

Emails are queued but not sent until the Q cluster worker runs:

```bash
python nbxdjango/manage.py qcluster
```

**Important:** The worker must be running in production for emails to be delivered.

### Sending Emails in Code

Use the utility function from `packagehandling.utils`:

```python
from packagehandling.utils import send_email

send_email(
    subject="Your Subject",
    body="Email body content",
    recipient_list=["user@example.com"],
)
```

This function:
- Queues the email asynchronously via Django-Q2
- Uses `DEFAULT_FROM_EMAIL` as the sender
- Returns immediately (non-blocking)

---

## When Emails Are Sent

### 1. Password Reset (`ForgotPassword` mutation)

**Trigger:** User requests password reset via GraphQL

**Mutation:**
```graphql
mutation {
  forgotPassword(email: "user@example.com") {
    ok
  }
}
```

**Email Content:**
- Subject: `Reset Your Password`
- Body: Contains a reset link with secure token
- Example: `http://localhost:3000/reset-password?uid=...&token=...`

**Security Notes:**
- Returns `ok: true` even if email doesn't exist (prevents user enumeration)
- Reset token is generated using Django's `PasswordResetTokenGenerator`

### 2. Consolidation Created (`CreateConsolidate` mutation)

**Trigger:** Admin creates a consolidation with `send_email: true`

**Mutation:**
```graphql
mutation {
  createConsolidate(
    description: "Monthly shipment"
    status: "pending"
    packageIds: [1, 2, 3]
    sendEmail: true
  ) {
    consolidate {
      id
      description
    }
  }
}
```

**Email Content:**
- Subject: `Consolidado creado`
- Body: `Tu consolidado ha sido creado exitosamente.`
- Recipient: The client's email address

**Notes:**
- `sendEmail` defaults to `false`
- Only superusers can create consolidations
- Email is only sent to the client who owns the packages

---

## Email Templates

Email templates are stored in `nbxdjango/packagehandling/emails/messages.py`:

```python
CONSOLIDATE_CREATED_SUBJECT = "Consolidado creado"
CONSOLIDATE_CREATED_MESSAGE = "Tu consolidado ha sido creado exitosamente."
```

**Current Limitations:**
- Emails are plain text only (no HTML)
- No template system (Django templates) is currently used

---

## Testing

### Manual Testing

1. Ensure environment variables are set
2. Start the Q cluster: `python nbxdjango/manage.py qcluster`
3. Trigger a password reset or create a consolidation with `send_email: true`
4. Check Mailgun logs for delivery status

### Unit Tests

Email sending is tested in:
- `nbxdjango/packagehandling/tests/mutations/test_auth_mutations.py`
- `nbxdjango/packagehandling/tests/mutations/test_consolidate_mutations.py`

Tests typically mock the `send_email` function to avoid actual email delivery.

---

## Troubleshooting

### Emails Not Being Sent

| Check | Command/Action |
|-------|----------------|
| Q cluster running? | `ps aux \| grep qcluster` |
| Env vars set? | `echo $MAILGUN_API_KEY` |
| Tasks in queue? | Check Django admin or Django-Q2 monitoring |
| Mailgun domain verified? | Check Mailgun dashboard |

### Common Issues

1. **"Task not processed"** → Q cluster worker not running
2. **"Authentication failed"** → Invalid Mailgun API key
3. **"Domain not found"** → Mailgun sender domain not configured or verified

---

## Future Enhancements

Potential improvements to the email system:

- [ ] HTML email templates using Django's template system
- [ ] Welcome email on user registration
- [ ] Package status change notifications
- [ ] Consolidation status updates (in_transit, delivered, etc.)
- [ ] Email delivery tracking/logging
- [ ] Unsubscribe links for marketing emails
