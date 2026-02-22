#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
python nbxdjango/manage.py migrate --noinput

# Check if superuser exists to determine if it's the first run
# We try to create the superuser. If it fails, we assume it's not the first run (or another error occurred).
# However, the script `create_superuser_script` already handles checking if it exists and just outputs a warning.
# To be robust, we'll check via Django shell if any user exists at all.

echo "Checking if initial data needs to be populated..."
if python nbxdjango/manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); exit(0 if User.objects.exists() else 1)"; then
    echo "Database already contains users. Skipping fake data generation."
else
    echo "Database is empty. Running first-time setup..."

    echo "Creating superuser..."
    python nbxdjango/manage.py create_superuser_script

    echo "Creating fake clients..."
    python nbxdjango/manage.py create_fake_clients

    echo "Creating fake users..."
    python nbxdjango/manage.py create_fake_users --count 10 --password password

    echo "Creating fake packages..."
    python nbxdjango/manage.py create_fake_packages

    echo "Creating fake consolidations..."
    python nbxdjango/manage.py create_fake_consolidations
fi

# Execute the passed command
exec "$@"
