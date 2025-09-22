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

To create fake packages for testing purposes, you can use the `create_fake_packages` management command.

Usage:

```bash
python nbxdjango/manage.py create_fake_packages <count>
```

Replace `<count>` with the number of fake packages you want to create.

Example:

```bash
python nbxdjango/manage.py create_fake_packages 10
```
