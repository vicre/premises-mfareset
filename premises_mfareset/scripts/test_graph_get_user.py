from pprint import pprint

from premises_mfareset.utils.graph import get_user


def run(*args):
    user_principal_name = args[0] if args else "<user>@dtu.dk"
    select_parameters = args[1] if len(args) > 1 else "$select=displayName,userPrincipalName,onPremisesImmutableId"

    print(f"Testing get_user() for: {user_principal_name}")
    print(f"Select: {select_parameters}")
    print()

    try:
        user = get_user(
            user_principal_name=user_principal_name,
            select_parameters=select_parameters,
        )
        pprint(user)
    except Exception as error:
        print(f"Error: {error}")