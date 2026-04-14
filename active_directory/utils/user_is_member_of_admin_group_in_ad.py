from .active_directory_query import active_directory_query

def user_is_member_of_admin_group_in_ad(user_upn: str) -> bool:
    groups_ou = "OU=MFAResetAdmins,OU=Groups,OU=SOC,OU=CIS,OU=AIT,DC=win,DC=dtu,DC=dk"

    users = active_directory_query(
        base_dn="DC=win,DC=dtu,DC=dk",
        search_filter=f"(&(objectClass=user)(userPrincipalName={user_upn}))",
        search_attributes=["distinguishedName", "cn"],
        limit=1,
    )

    if not users:
        print(f"User not found: {user_upn}")
        return False

    user_dn = users[0]["distinguishedName"][0]

    groups = active_directory_query(
        base_dn=groups_ou,
        search_filter="(objectClass=group)",
        search_attributes=["distinguishedName", "cn", "member"],
    )

    for group in groups:
        group_name = group.get("cn", ["<unknown>"])[0]
        members = group.get("member", [])

        if user_dn in members:
            print(f"User is member of group: {group_name}")
            return True

    return False