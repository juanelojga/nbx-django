# nbx-django

This is a Django project for managing packages.

## Local Development Setup

### 1. Prerequisites

*   Python 3.11
*   PostgreSQL

### 2. Initial Setup

a. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd nbx-django
   ```

b. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

c. **Set up environment variables:**

   Create a `.env` file in the project root by copying the example file:
   ```bash
   cp .env.example .env
   ```

   Now, edit the `.env` file and fill in the required values:
   *   `SECRET_KEY`: A new secret key for your local environment.
   *   `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: Your local PostgreSQL connection details.
   *   `MAILGUN_API_KEY`, `MAILGUN_SENDER_DOMAIN`: Your Mailgun credentials (optional, for email sending).

### 3. Database Setup

Run the database migrations to set up your local database schema:
```bash
python nbxdjango/manage.py migrate
```

### 4. Running the Development Server

Start the Django development server:
```bash
python nbxdjango/manage.py runserver
```
The application will be available at `http://127.0.0.1:8000/`.

The interactive GraphQL interface is available at `http://127.0.0.1:8000/graphql` and is automatically enabled in the development environment (`DEBUG=True`).

For complete GraphQL API documentation, see [GRAPHQL_API.md](./GRAPHQL_API.md).

## Deployment (Railway)

This project is configured for continuous deployment to [Railway](https://railway.app/) via GitHub Actions.

### How it Works

1.  **CI/CD Pipeline**: The workflow is defined in `.github/workflows/ci.yml`.
2.  **Triggers**: A push or merge to the `main` branch will trigger the pipeline.
3.  **Testing**: The pipeline first installs dependencies, runs database migrations on a test database, and executes the test suite using `pytest`.
4.  **Deployment**: If the tests pass, the `deploy` job uses the [Railway CLI Action](https://github.com/railwayapp/railway-action) to deploy the application.
5.  **Release Phase**: Before the new version goes live, Railway runs the `release` command from the `Procfile` (`python nbxdjango/manage.py migrate`) to run production database migrations.
6.  **Web Process**: The application is served by `gunicorn`, as defined in the `web` command of the `Procfile`.

### Production Environment Variables

The following environment variables must be set in the Railway project settings:

*   `DATABASE_URL`: Provided by the Railway PostgreSQL service.
*   `SECRET_KEY`: A strong, randomly generated secret key.
*   `ALLOWED_HOSTS`: The domain provided by Railway (e.g., `web-production-xxxx.up.railway.app`).
*   `DEBUG`: Set to `False`.
*   `MAILGUN_API_KEY`: Your Mailgun API key.
*   `MAILGUN_SENDER_DOMAIN`: Your Mailgun sender domain.

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

To populate the database with fake data for testing and development purposes, use the following management commands. These commands use [factory_boy](https://factoryboy.readthedocs.io/) and [Faker](https://faker.readthedocs.io/) to generate realistic test data.

### Available Commands

| Command | Description |
|---------|-------------|
| `create_fake_users` | Creates fake users (without clients) |
| `create_fake_clients` | Creates fake clients (each with an associated user) |
| `create_fake_packages` | Creates fake packages for clients |
| `create_fake_consolidations` | Creates fake consolidations (can include packages) |

### Creating Fake Users

Create users without associated clients:

```bash
# Create 10 users with default password 'password'
python nbxdjango/manage.py create_fake_users

# Create 5 users with custom password
python nbxdjango/manage.py create_fake_users --count 5 --password mypass123
```

### Creating Fake Clients

Create clients (each client automatically creates an associated user):

```bash
# Create 10 clients (default)
python nbxdjango/manage.py create_fake_clients

# Create 5 clients
python nbxdjango/manage.py create_fake_clients --count 5
```

### Creating Fake Packages

Create packages with various options:

```bash
# Create 100 packages distributed across random clients (default)
python nbxdjango/manage.py create_fake_packages

# Create 50 packages for a specific client by ID
python nbxdjango/manage.py create_fake_packages --count 50 --client-id 1

# Create packages for a specific client by email
python nbxdjango/manage.py create_fake_packages --count 20 --client-email "user@example.com"

# Create packages and assign them to a specific consolidation
python nbxdjango/manage.py create_fake_packages --count 10 --consolidate-id 1

# Create packages with random assignment to existing consolidations (50% chance)
python nbxdjango/manage.py create_fake_packages --count 30 --client-id 1 --with-consolidation
```

**Note:** The `--consolidate-id` option automatically uses the consolidation's client. If you also specify `--client-id`, they must match.

### Creating Fake Consolidations

Create consolidations with optional packages:

```bash
# Create 10 consolidations for random clients (default)
python nbxdjango/manage.py create_fake_consolidations

# Create 5 consolidations for a specific client
python nbxdjango/manage.py create_fake_consolidations --count 5 --client-id 1

# Create consolidations with packages (3 packages each)
python nbxdjango/manage.py create_fake_consolidations --count 3 --packages 3

# Create consolidations with random package counts (1-5 packages each)
python nbxdjango/manage.py create_fake_consolidations --count 5 --packages-min 1 --packages-max 5 --packages 1
```

### Complete Example Workflow

Here's a complete example of setting up test data:

```bash
# 1. Create some clients (each gets a user automatically)
python nbxdjango/manage.py create_fake_clients --count 5

# 2. Create some additional standalone users
python nbxdjango/manage.py create_fake_users --count 3 --password testpass

# 3. Create consolidations with packages for client #1
python nbxdjango/manage.py create_fake_consolidations \
    --count 3 \
    --client-id 1 \
    --packages-min 2 \
    --packages-max 5 \
    --packages 1

# 4. Create additional standalone packages for client #1
python nbxdjango/manage.py create_fake_packages \
    --count 20 \
    --client-id 1 \
    --with-consolidation
```

### Command Help

For detailed help on any command, use:

```bash
python nbxdjango/manage.py create_fake_users --help
python nbxdjango/manage.py create_fake_clients --help
python nbxdjango/manage.py create_fake_packages --help
python nbxdjango/manage.py create_fake_consolidations --help
```

## Running Tests

This project uses `pytest` with `pytest-django` for testing.

1.  Install testing dependencies:

    ```bash
    pip install -r requirements-dev.txt
    ```

2.  Run all tests from the `nbxdjango` directory:

    ```bash
    DJANGO_SETTINGS_MODULE=nbxdjango.settings DATABASE_URL=postgres://myuser:mypassword@localhost:5432/mydatabase pytest nbxdjango/packagehandling/tests/
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