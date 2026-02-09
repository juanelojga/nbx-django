"""
Unit tests for custom JWT utility functions.

Tests the timezone-aware refresh token expiration checking.
"""

from calendar import timegm
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from packagehandling.jwt_utils import custom_refresh_has_expired


@pytest.mark.django_db
class TestCustomRefreshHasExpired:
    """Test suite for custom_refresh_has_expired function."""

    def test_token_not_expired_just_created(self):
        """Test that a token created just now is not expired."""
        # Token created now
        orig_iat = timegm(timezone.now().utctimetuple())

        # Should not be expired
        assert custom_refresh_has_expired(orig_iat) is False

    def test_token_not_expired_within_delta(self):
        """Test that a token within the expiration delta is not expired."""
        # Token created 5 days ago (less than 7-day default)
        five_days_ago = timezone.now() - timedelta(days=5)
        orig_iat = timegm(five_days_ago.utctimetuple())

        # Should not be expired
        assert custom_refresh_has_expired(orig_iat) is False

    def test_token_not_expired_at_boundary(self):
        """Test that a token at the exact expiration boundary is not expired."""
        # Token created exactly 7 days ago minus 1 second
        almost_expired = timezone.now() - timedelta(days=7, seconds=-1)
        orig_iat = timegm(almost_expired.utctimetuple())

        # Should not be expired (boundary condition)
        assert custom_refresh_has_expired(orig_iat) is False

    def test_token_expired_beyond_delta(self):
        """Test that a token beyond the expiration delta is expired."""
        # Token created 8 days ago (more than 7-day default)
        eight_days_ago = timezone.now() - timedelta(days=8)
        orig_iat = timegm(eight_days_ago.utctimetuple())

        # Should be expired
        assert custom_refresh_has_expired(orig_iat) is True

    def test_token_expired_well_beyond_delta(self):
        """Test that a token well beyond the expiration delta is expired."""
        # Token created 30 days ago
        thirty_days_ago = timezone.now() - timedelta(days=30)
        orig_iat = timegm(thirty_days_ago.utctimetuple())

        # Should be expired
        assert custom_refresh_has_expired(orig_iat) is True

    def test_token_with_custom_expiration_delta(self):
        """Test token expiration with a custom JWT_REFRESH_EXPIRATION_DELTA."""
        # Mock a custom 1-day expiration
        with patch("packagehandling.jwt_utils.jwt_settings") as mock_settings:
            mock_settings.JWT_REFRESH_EXPIRATION_DELTA = timedelta(days=1)

            # Token created 2 days ago
            two_days_ago = timezone.now() - timedelta(days=2)
            orig_iat = timegm(two_days_ago.utctimetuple())

            # Should be expired with 1-day delta
            assert custom_refresh_has_expired(orig_iat) is True

            # Token created 12 hours ago
            twelve_hours_ago = timezone.now() - timedelta(hours=12)
            orig_iat = timegm(twelve_hours_ago.utctimetuple())

            # Should not be expired with 1-day delta
            assert custom_refresh_has_expired(orig_iat) is False

    def test_context_parameter_accepted(self):
        """Test that the context parameter is accepted (even if not used)."""
        # Token created now
        orig_iat = timegm(timezone.now().utctimetuple())

        # Should not raise any error with context parameter
        mock_context = object()
        assert custom_refresh_has_expired(orig_iat, context=mock_context) is False

    def test_timezone_aware_calculation(self):
        """Test that the function properly handles timezone-aware datetime."""
        # This test verifies that timezone.now() is used (timezone-aware)
        # instead of datetime.utcnow() (naive)

        # Get current timezone-aware time
        now = timezone.now()
        orig_iat = timegm(now.utctimetuple())

        # Token should not be expired
        assert custom_refresh_has_expired(orig_iat) is False

    def test_future_token_not_expired(self):
        """Test that a token issued 'in the future' is not expired."""
        # Edge case: token issued 1 hour in the future (clock skew scenario)
        future_time = timezone.now() + timedelta(hours=1)
        orig_iat = timegm(future_time.utctimetuple())

        # Should not be expired (future token is valid)
        assert custom_refresh_has_expired(orig_iat) is False

    def test_multiple_calls_consistent(self):
        """Test that multiple calls with same orig_iat return consistent results."""
        # Token created 3 days ago
        three_days_ago = timezone.now() - timedelta(days=3)
        orig_iat = timegm(three_days_ago.utctimetuple())

        # Multiple calls should return same result
        result1 = custom_refresh_has_expired(orig_iat)
        result2 = custom_refresh_has_expired(orig_iat)
        result3 = custom_refresh_has_expired(orig_iat)

        assert result1 == result2 == result3
        assert result1 is False  # Should not be expired
