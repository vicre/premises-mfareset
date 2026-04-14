from active_directory.utils.azure_user_is_synced_with_on_premise_user import (
    azure_user_is_synced_with_on_premise_user,
)
from premises_mfareset.utils.graph import get_user
from active_directory.utils.active_directory_query import active_directory_query
from active_directory.utils.user_is_member_of_admin_group_in_ad import user_is_member_of_admin_group_in_ad

def run(*args):
    user_input = args[0]

    azure_user_principal_name = user_input
    sam_accountname = user_input.split("@", 1)[0]
 

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
        user_principal_name=azure_user_principal_name,
        on_premises_immutable_id=on_premises_immutable_id,
    )

    user_is_member = user_is_member_of_admin_group_in_ad(azure_user_principal_name)
    # users = active_directory_query(
    #     base_dn="DC=win,DC=dtu,DC=dk",
    #     search_filter="(&(objectClass=user)(userPrincipalName=vicre@dtu.dk))",
    #     search_attributes=["distinguishedName", "userPrincipalName", "cn"],
    #     limit=1,
    # )
    # user_dn = users[0]["distinguishedName"][0]
    # groups = active_directory_query(
    #     base_dn="OU=MFAResetAdmins,OU=Groups,OU=SOC,OU=CIS,OU=AIT,DC=win,DC=dtu,DC=dk",
    #     search_filter="(objectClass=group)",
    #     search_attributes=["distinguishedName", "cn"],
    # )


    # for group in groups:
    #         group_name = group.get("cn", ["<unknown>"])[0]
    #         members = group.get("member", [])

    #         if user_dn in members:
    #             print(f"User is member of group: {group_name}")
    #             break


    if is_synced and user_is_member:
        print("User is authenticated / synced")
    else:
        print("User is not authenticated / not synced")