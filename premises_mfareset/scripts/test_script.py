from premises_mfareset.utils.auth_methods import prepare_auth_methods
from premises_mfareset.utils.graph import list_user_authentication_methods

from .test_get_user_mfa_admin_groups import test_get_user_mfa_admin_groups
from active_directory.utils.active_directory_query import active_directory_query

def run(*args):
    email = args[0] if args else None

    if not email:
        print("Missing email")
        return

    TARGET_USER = "testtes@dtu.dk"

    groups = test_get_user_mfa_admin_groups(*args)

    allowed_ous = []

    for group in groups:
        ea_list = group.get("extensionAttribute1", [])

        if not ea_list:
            continue

        ea_value = ea_list[0]

        for ou in ea_value.split(","):
            ou = ou.strip()
            if ou and ou not in allowed_ous:
                allowed_ous.append(ou)

    allowed_ous_unique = allowed_ous

    print("allowed_ous_unique >>", allowed_ous_unique)
    print()

    # Find target user in AD
    target_user_filter = f"(&(objectClass=user)(userPrincipalName={TARGET_USER}))"
    target_user_attrs = ["distinguishedName", "cn", "userPrincipalName"]

    target_users = active_directory_query(
        base_dn="DC=win,DC=dtu,DC=dk",
        search_filter=target_user_filter,
        search_attributes=target_user_attrs,
        limit=1,
    )

    if not target_users:
        print(f"Target user not found: {TARGET_USER}")
        return

    target_dn_list = target_users[0].get("distinguishedName", [])
    target_dn = target_dn_list[0] if target_dn_list else ""

    print("Target user DN:")
    print(target_dn)
    print()

    is_allowed = False
    matched_ou = None

    for allowed_ou in allowed_ous_unique:
        expected_fragment = f",OU={allowed_ou},OU=DTUBaseUsers,DC=win,DC=dtu,DC=dk"
        if expected_fragment.lower() in target_dn.lower():
            is_allowed = True
            matched_ou = allowed_ou
            break

    if is_allowed:
        print(f"ALLOWED: target user is inside OU '{matched_ou}'")

        from premises_mfareset.utils.reset_mfa import reset_mfa_methods

        methods = list_user_authentication_methods(TARGET_USER)
        mfa_methods = prepare_auth_methods(methods)

        print(methods)
        print(mfa_methods)
        message = reset_mfa_methods(TARGET_USER, mfa_methods)

        print(message)
    else:
        print("NOT ALLOWED: target user is not inside any allowed OU")