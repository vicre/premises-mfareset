from active_directory.utils.azure_user_is_synced_with_on_premise_user import (
    azure_user_is_synced_with_on_premise_user,
)
from premises_mfareset.utils.graph import get_user


def run(*args):
    user_input = args[0]

    if "@" in user_input:
        azure_user_principal_name = user_input
        sam_accountname = user_input.split("@", 1)[0]
    else:
        sam_accountname = user_input
        azure_user_principal_name = f"{sam_accountname}@dtu.dk"

    select_param = "$select=onPremisesImmutableId"

    print(f"Testing user: {azure_user_principal_name}")
    print(f"Using sAMAccountName: {sam_accountname}")

    try:
        response = get_user(
            user_principal_name=azure_user_principal_name,
            select_parameters=select_param,
        )
    except Exception as error:
        print("User not found in Azure")
        print("Error:", error)
        return

    on_premises_immutable_id = response.get("onPremisesImmutableId")
    print("Azure onPremisesImmutableId:", on_premises_immutable_id)

    is_synced = azure_user_is_synced_with_on_premise_user(
        sam_accountname=sam_accountname,
        on_premises_immutable_id=on_premises_immutable_id,
    )

    if is_synced:
        print("User is authenticated / synced")
    else:
        print("User is not authenticated / not synced")