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

## Email Setup (Mailgun)

This project uses Mailgun for sending emails. Follow these steps to configure it.

### 1. Install Required Packages

Install `django-anymail` (with Mailgun support) and `python-dotenv`.

```bash
pip install "django-anymail[mailgun]" python-dotenv
```

These packages are included in `requirements.txt`.

### 2. Set Environment Variables

Create a `.env` file in the project root directory with your Mailgun credentials:

```
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_SENDER_DOMAIN=your-mailgun-sender-domain
```

**Note:** The `.env` file is included in `.gitignore` and should not be committed to version control.

### 3. How It's Configured

-   **`settings.py`**: The `EMAIL_BACKEND` is set to `anymail.backends.mailgun.EmailBackend`. It reads your Mailgun credentials from the environment variables.
-   **`manage.py` & `wsgi.py`**: These files are configured to load the environment variables from the `.env` file using `python-dotenv`.

### 4. Sending Emails

A utility function `send_email(subject, body, recipient_list)` is available in `nbxdjango/packagehandling/utils.py`. You can use it throughout the project to send emails.

**Example Usage (in Django Shell):**

1.  Open the shell:
    ```bash
    python nbxdjango/manage.py shell
    ```

2.  Send an email:
    ```python
    from packagehandling.utils import send_email
    send_email("Test Subject", "This is a test email.", ["recipient@example.com"])
    ```

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