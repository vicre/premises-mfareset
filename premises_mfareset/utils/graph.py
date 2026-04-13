import os
from typing import Any

import msal
import requests


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing or empty environment variable: {name}")
    return value


TENANT_ID = require_env("AZURE_TENANT_ID")
CLIENT_ID = require_env("AZURE_APP_REGISTRATION_CLIENT_ID")
CLIENT_SECRET = require_env("AZURE_APP_REGISTRATION_CLIENT_SECRET")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]

# In-memory app token cache is handled by MSAL automatically.
_msal_app = msal.ConfidentialClientApplication(
    client_id=CLIENT_ID,
    client_credential=CLIENT_SECRET,
    authority=AUTHORITY,
)


def get_app_access_token() -> str:
    result = _msal_app.acquire_token_for_client(scopes=SCOPES)
    if "access_token" not in result:
        raise RuntimeError(
            f"Failed to acquire Graph token: "
            f"{result.get('error')} - {result.get('error_description')}"
        )
    return result["access_token"]


def graph_get(url: str) -> dict[str, Any]:
    token = get_app_access_token()
    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


# A helper function used in delete_user_authentication_method() below
def graph_delete(url: str) -> None:
    token = get_app_access_token()
    response = requests.delete(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        timeout=30,
    )

    if response.status_code != 204:
        raise RuntimeError(
            f"Graph DELETE failed: {response.status_code} - {response.text}"
        )



def list_user_authentication_methods(user_principal_name: str) -> list[dict[str, Any]]:
    url = (
        "https://graph.microsoft.com/v1.0/"
        f"users/{user_principal_name}/authentication/methods"
    )
    data = graph_get(url)
    return data.get("value", [])


def delete_user_authentication_method(
    user_principal_name: str,
    authentication_method_id: str,
    authentication_method_type: str,
) -> None:
    base_url = (
        "https://graph.microsoft.com/v1.0/"
        f"users/{user_principal_name}/authentication"
    )

    if authentication_method_type.endswith("phoneAuthenticationMethod"):
        url = f"{base_url}/phoneMethods/{authentication_method_id}"

    elif authentication_method_type.endswith("softwareOathAuthenticationMethod"):
        url = f"{base_url}/softwareOathMethods/{authentication_method_id}"

    elif authentication_method_type.endswith("microsoftAuthenticatorAuthenticationMethod"):
        url = f"{base_url}/microsoftAuthenticatorMethods/{authentication_method_id}"

    else:
        raise ValueError(
            f"Unsupported deletable authentication method type: "
            f"{authentication_method_type}"
        )

    graph_delete(url)


# Used by .active_directory.utils.azure_user_is_synced_with_on_premise_user
def get_user(
    *,
    user_principal_name: str,
    select_parameters: str | None = None,
) -> dict[str, Any]:
    """
    Example:
        get_user(
            user_principal_name="<user>@dtu.dk",
            select_parameters="$select=onPremisesImmutableId"
        )
    """
    if select_parameters:
        url = (
            "https://graph.microsoft.com/v1.0/"
            f"users/{user_principal_name}?{select_parameters}"
        )
    else:
        url = f"https://graph.microsoft.com/v1.0/users/{user_principal_name}"

    return graph_get(url)