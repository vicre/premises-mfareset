from active_directory.utils.active_directory_query import active_directory_query
from premises_mfareset.utils.graph import get_user


def convert_to_base64(byte_data):
    import base64
    return base64.b64encode(byte_data).decode("utf-8")


def azure_user_is_synced_with_on_premise_user(
    user_principal_name: str,
    on_premises_immutable_id: str,
) -> bool:
    base_dn = "DC=win,DC=dtu,DC=dk"
    search_filter = f"(UserPrincipalName={user_principal_name})"
    search_attributes = ["mS-DS-ConsistencyGuid"]

    active_directory_response = active_directory_query(
        base_dn=base_dn,
        search_filter=search_filter,
        search_attributes=search_attributes,
        limit=1,
    )

    try:
        ms_ds_consistency_guid = convert_to_base64(
            active_directory_response[0]["mS-DS-ConsistencyGuid"][0]
        )
    except IndexError:
        print("AD user not found or mS-DS-ConsistencyGuid missing")
        return False

    print("AD mS-DS-ConsistencyGuid:", ms_ds_consistency_guid)
    print("Azure onPremisesImmutableId:", on_premises_immutable_id)

    return ms_ds_consistency_guid == on_premises_immutable_id


