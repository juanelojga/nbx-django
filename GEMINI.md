# Gemini

This project is a Django-based application for package handling.

## Running Tests

To run the tests, use the following command:

```bash
DJANGO_SETTINGS_MODULE=nbxdjango.settings pytest nbxdjango/packagehandling/tests/
```

## Implemented Fixes

- Fixed a bug in the `CustomRevokeToken` mutation where an incorrect setting was used for the refresh token cookie name.
- Corrected the test suite to properly handle Django settings and test discovery.
