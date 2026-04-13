import os
import msal


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing or empty environment variable: {name}")
    return value


TENANT_ID = require_env("AZURE_TENANT_ID")
CLIENT_ID = require_env("AZURE_APP_REGISTRATION_CLIENT_ID")
CLIENT_SECRET = require_env("AZURE_APP_REGISTRATION_CLIENT_SECRET")
REDIRECT_URI = require_env("AZURE_REDIRECT_URI")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["User.Read"]


def build_msal_app():
    return msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY,
    )


def build_auth_url():
    app = build_msal_app()
    return app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        prompt="select_account",
    )


def acquire_token_by_auth_code(code: str):
    app = build_msal_app()
    return app.acquire_token_by_authorization_code(
        code=code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )