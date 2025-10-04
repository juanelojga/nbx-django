import pytest
from django.db.utils import IntegrityError
from packagehandling.models.user import CustomUser


@pytest.mark.django_db
def test_customuser_creation():
    user = CustomUser.objects.create_user(
        email="test@example.com",
        password="password123",
        first_name="Test",
        last_name="User",
    )
    assert user.email == "test@example.com"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.check_password("password123")
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.username is None  # username should be None by default when not provided


@pytest.mark.django_db
def test_customuser_str_method():
    user = CustomUser.objects.create_user(
        email="strtest@example.com", password="password123"
    )
    assert str(user) == "strtest@example.com"


@pytest.mark.django_db
def test_customuser_unique_email_constraint():
    CustomUser.objects.create_user(email="unique@example.com", password="password123")
    with pytest.raises(IntegrityError):
        CustomUser.objects.create_user(
            email="unique@example.com", password="anotherpassword"
        )


@pytest.mark.django_db
def test_customuser_username_nullable():
    user = CustomUser.objects.create_user(
        email="nullable@example.com", password="password123"
    )
    assert user.username is None


@pytest.mark.django_db
def test_customuser_username_blank():
    user = CustomUser.objects.create_user(
        email="blank@example.com", password="password123", username=""
    )
    assert user.username == ""


@pytest.mark.django_db
def test_customuser_unique_username_constraint():
    CustomUser.objects.create_user(
        email="user1@example.com", password="password123", username="unique_user"
    )
    with pytest.raises(IntegrityError):
        CustomUser.objects.create_user(
            email="user2@example.com",
            password="anotherpassword",
            username="unique_user",
        )


@pytest.mark.django_db
def test_customuser_create_superuser():
    superuser = CustomUser.objects.create_superuser(
        email="admin@example.com",
        password="adminpassword",
    )
    assert superuser.email == "admin@example.com"
    assert superuser.check_password("adminpassword")
    assert superuser.is_active is True
    assert superuser.is_staff is True
    assert superuser.is_superuser is True
    assert (
        superuser.username is None
    )  # username should be None by default when not provided
