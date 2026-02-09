"""
Custom JWT utility functions for handling refresh token expiration.

This module provides timezone-aware JWT refresh token expiration checking
to fix the bug in django-graphql-jwt's default implementation which uses
naive datetime (datetime.utcnow()) instead of timezone-aware datetime.
"""

from calendar import timegm

from django.utils import timezone
from graphql_jwt.settings import jwt_settings


def custom_refresh_has_expired(orig_iat, context=None):
    """
    Check if a refresh token has expired using timezone-aware datetime.

    This function overrides the default graphql-jwt implementation to properly
    handle timezone-aware datetime comparisons. The default implementation uses
    datetime.utcnow() which returns naive datetime, causing incorrect expiration
    calculations when compared with Django's timezone-aware datetimes.

    Args:
        orig_iat (int): Original issued-at timestamp (Unix timestamp)
        context: Optional request context (not used but kept for compatibility)

    Returns:
        bool: True if the refresh token has expired, False otherwise

    Technical Notes:
        - Uses Django's timezone.now() for timezone-aware current time
        - Converts to UTC before comparison for consistency
        - JWT_REFRESH_EXPIRATION_DELTA is configured in settings (default: 7 days)
    """
    # Calculate expiration timestamp by adding refresh delta to original issued time
    exp = orig_iat + jwt_settings.JWT_REFRESH_EXPIRATION_DELTA.total_seconds()

    # Get current time as timezone-aware datetime and convert to Unix timestamp
    current_timestamp = timegm(timezone.now().utctimetuple())

    # Token is expired if current time is greater than expiration time
    return current_timestamp > exp
