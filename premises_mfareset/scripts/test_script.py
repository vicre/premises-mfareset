from .test_get_user_mfa_admin_groups import test_get_user_mfa_admin_groups

def run(*args):
    email = args[0] if args else None

    if not email:
        print("Missing email")
        return

    test_get_user_mfa_admin_groups(*args)


    pass