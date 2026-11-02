"""Isolated test configuration: fake credentials and an in-memory database."""
import os

for name, value in {
    "DJANGO_SECRET_KEY": "local-tests-only-not-a-production-secret-key",
    "DJANGO_DEBUG": "false",
    "AZURE_TENANT_ID": "00000000-0000-0000-0000-000000000000",
    "AZURE_APP_REGISTRATION_CLIENT_ID": "00000000-0000-0000-0000-000000000001",
    "AZURE_APP_REGISTRATION_CLIENT_SECRET": "test-only",
    "AZURE_REDIRECT_URI": "http://localhost:8000/auth/callback/",
    "ACTIVE_DIRECTORY_USERNAME": "test-only",
    "ACTIVE_DIRECTORY_PASSWORD": "test-only",
    "ACTIVE_DIRECTORY_SERVER": "ad.invalid",
    "LOG_LEVEL_DJANGO": "CRITICAL",
}.items():
    os.environ[name] = value

from .settings import *  # noqa: E402,F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
TEST_RUNNER = "config.test_runner.OfflineTestRunner"
