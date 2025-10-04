# nbx-django

This is a Django project for managing packages.

## Getting Started

1.  Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

2.  Run the database migrations:

    ```bash
    python nbxdjango/manage.py migrate
    ```

3.  Start the development server:

    ```bash
    python nbxdjango/manage.py runserver
    ```

## Asynchronous Email Setup (Django-Q + Mailgun)

This project uses **Django-Q** to queue emails and **Mailgun** to send them. This prevents slow email API calls from blocking user requests.

### 1. How It Works

1.  **Queueing:** When an email needs to be sent, the `send_email` utility function adds the email to a queue using `Django-Q` instead of sending it immediately.
2.  **Processing:** A separate worker process, the `qcluster`, runs in the background, monitoring the queue.
3.  **Sending:** When the `qcluster` finds a new email task, it processes it and sends the email via the Mailgun API.

### 2. Setup and Configuration

#### a. Install Required Packages

Install `django-q`, `django-anymail` (with Mailgun support), and `python-dotenv`.

```bash
pip install django-q "django-anymail[mailgun]" python-dotenv
```

These packages are included in `requirements.txt`.

#### b. Set Environment Variables

Create a `.env` file in the project root with your Mailgun credentials:

```
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_SENDER_DOMAIN=your-mailgun-sender-domain
```

An example file is provided at `.env.example`. The `.env` file is ignored by Git.

#### c. Run Migrations

Django-Q requires its own database tables to manage the queue. Run the migrations to create them:

```bash
python nbxdjango/manage.py migrate
```

### 3. Running the Worker

To process the email queue, you must run the `qcluster` worker. Open a **separate terminal** and run:

```bash
python nbxdjango/manage.py qcluster
```

This process must be running for emails to be sent.

### 4. Sending Emails

The `send_email(subject, body, recipient_list)` utility function in `nbxdjango/packagehandling/utils.py` now automatically queues the email to be sent asynchronously.

**Example Usage (in Django Shell):**

1.  Open the shell:
    ```bash
    python nbxdjango/manage.py shell
    ```

2.  Queue an email for sending:
    ```python
    from packagehandling.utils import send_email
    send_email("Test Subject", "This is a test email.", ["recipient@example.com"])
    ```

The email will be added to the queue and sent by the `qcluster` process.

## Creating Fake Data

To create fake clients, users, and packages for testing purposes, you can use the `create_fake_packages` management command.

Usage:

```bash
python nbxdjango/manage.py create_fake_packages
```

This command will create 10 fake clients (each with an associated user) and 100 fake packages, randomly assigned to these clients.

## Running Tests

This project uses `pytest` with `pytest-django` for testing.

1.  Install testing dependencies:

    ```bash
    pip install pytest pytest-django
    ```

2.  Set the `DJANGO_SETTINGS_MODULE` environment variable and run all tests:

    ```bash
    DJANGO_SETTINGS_MODULE=nbxdjango.settings pytest
    ```

3.  Run tests for a specific app (e.g., `packagehandling`):

    ```bash
    DJANGO_SETTINGS_MODULE=nbxdjango.settings pytest nbxdjango/packagehandling/tests/
    ```

4.  Run tests for a specific file (e.g., `test_customuser.py`):

    ```bash
    DJANGO_SETTINGS_MODULE=nbxdjango.settings pytest nbxdjango/packagehandling/tests/models/test_customuser.py
    ```

## Running Linters Locally

To maintain code quality, you can run the following linters and formatters locally:

### Check for style issues
flake8 .

### Auto-format code
black .

### Organize imports
isort .

### Type checking
mypy .

### Precommit Hook
pre-commit install
pre-commit run --all-file

## Creating a Superuser Non-Interactively

To create a superuser non-interactively, you can use the `create_superuser_script` management command. This method is ideal for automated tasks and deployment scripts as it does not require manual input.

### 1. Set Environment Variables

For security, the script reads the superuser's credentials from environment variables.

```bash
export DJANGO_SUPERUSER_USERNAME=your_username
export DJANGO_SUPERUSER_EMAIL=your_email@example.com
export DJANGO_SUPERUSER_PASSWORD=your_password
```

### 2. Run the Script

Once the environment variables are set, run the following command from your project's root directory:

```bash
python nbxdjango/manage.py create_superuser_script
```

### 3. One-Liner Command

For automation, you can combine setting the environment variables and running the script into a single command:

```bash
DJANGO_SUPERUSER_USERNAME=your_username DJANGO_SUPERUSER_EMAIL=your_email@example.com DJANGO_SUPERUSER_PASSWORD=your_password python nbxdjango/manage.py create_superuser_script
```

### Why Use This Method?

The standard `createsuperuser` command is interactive, meaning it prompts you to enter the username, email, and password. This is not suitable for automated processes like deployment scripts or continuous integration (CI) pipelines. The `create_superuser_script` command is non-interactive and can be executed without manual intervention, making it perfect for these scenarios.
