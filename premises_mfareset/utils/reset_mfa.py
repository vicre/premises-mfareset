import time
from typing import Any

from premises_mfareset.utils.graph import (
    delete_user_authentication_method,
    list_user_authentication_methods,
)
from premises_mfareset.utils.auth_methods import prepare_auth_methods


def reset_mfa_methods(
    upn: str,
    methods_to_delete: list[dict[str, Any]],
    verify_retries: int = 10,
    verify_delay_seconds: float = 2.0,
) -> str:
    """
    Deletes MFA methods one at a time.
    After each delete, re-queries Graph and confirms the method id is gone
    before continuing to the next one.
    """

    if not methods_to_delete:
        return "No MFA methods to delete."

    for method in methods_to_delete:
        method_id = method["id"]
        method_type = method["type"]
        label = method.get("label", method_type)

        delete_user_authentication_method(
            user_principal_name=upn,
            authentication_method_id=method_id,
            authentication_method_type=method_type,
        )

        confirmed_deleted = False

        for attempt in range(verify_retries):
            current_methods = list_user_authentication_methods(upn)
            current_pretty = prepare_auth_methods(current_methods)
            current_ids = {m["id"] for m in current_pretty}

            if method_id not in current_ids:
                confirmed_deleted = True
                break

            time.sleep(verify_delay_seconds)

        if not confirmed_deleted:
            raise RuntimeError(
                f"Delete call succeeded for '{label}' ({method_id}), "
                f"but verification failed because the method still appears present."
            )

    return "MFA methods successfully reset."