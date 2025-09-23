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

## Creating Fake Data

To create fake clients, users, and packages for testing purposes, you can use the `create_fake_packages` management command.

Usage:

```bash
python nbxdjango/manage.py create_fake_packages
```

This command will create 10 fake clients (each with an associated user) and 100 fake packages, randomly assigned to these clients.

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
