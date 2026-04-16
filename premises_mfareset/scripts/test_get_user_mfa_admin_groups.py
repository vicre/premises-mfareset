from active_directory.utils.active_directory_query import active_directory_query

MFA_ADMIN_GROUPS_OU = "OU=MFAResetAdmins,OU=Groups,OU=SOC,OU=CIS,OU=AIT,DC=win,DC=dtu,DC=dk"

def test_get_user_mfa_admin_groups(user_upn: str):
    """
    Return all groups under MFAResetAdmins OU that the user is a member of.
    Includes nested membership via LDAP_MATCHING_RULE_IN_CHAIN.
    """
    if not user_upn:
        print("Missing user_upn")
        return []

    # 1) Find the user DN from the UPN
    user_search_filter = f"(&(objectClass=user)(userPrincipalName={user_upn}))"
    user_attrs = ["distinguishedName", "cn", "userPrincipalName"]

    users = active_directory_query(
        base_dn="DC=win,DC=dtu,DC=dk",
        search_filter=user_search_filter,
        search_attributes=user_attrs,
        limit=1,
    )

    if not users:
        print(f"User not found: {user_upn}")
        return []

    user_dn = users[0]["distinguishedName"][0] # e.g User DN: CN=testtes,OU=XYZ,OU=ABC,DC=win,DC=dtu,DC=dk
    print(f"User DN: {user_dn}")

    # 2) Find all groups in the MFAResetAdmins OU where the user is a member
    #    1.2.840.113556.1.4.1941 = recursive/nested membership check
    group_search_filter = (
        f"(&(objectClass=group)"
        f"(member:1.2.840.113556.1.4.1941:={user_dn}))"
    )

    group_attrs = ["cn", "distinguishedName", "description", "extensionAttribute1"]

    groups = active_directory_query(
        base_dn=MFA_ADMIN_GROUPS_OU,
        search_filter=group_search_filter,
        search_attributes=group_attrs,
        limit=None,
    )

    print(f"Found {len(groups)} MFA admin group(s) for {user_upn}")

    for group in groups:
        cn = group.get("cn", ["<no cn>"])[0]
        dn = group.get("distinguishedName", ["<no dn>"])[0]
        ea = group.get("extensionAttribute1", ["<no ea>"])[0]
        print(f"- {cn}")
        print(f"  {dn}")
        print(f"  {ea}")

    return groups