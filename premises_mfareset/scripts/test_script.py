from pprint import pprint

from active_directory.utils.active_directory_connect import active_directory_connect
from active_directory.utils.active_directory_query import active_directory_query
from premises_mfareset.scripts.test_sync_user import run as sync_user

def run(*args):
    email = args[0] if args else None

    if not email:
        print("Missing email")
        return

    sync_user(email)
    

    # print("=== Testing AD connection ===")

    # conn, message = active_directory_connect()
    # print(message)

    # if not conn:
    #     print("Connection failed, stopping test.")
    #     return

    # print("\n=== Testing AD query (users) ===")

    # base_dn = "DC=win,DC=dtu,DC=dk"
    # search_filter = "(objectClass=user)"
    # limit = 5

    # users = active_directory_query(
    #     base_dn=base_dn,
    #     search_filter=search_filter,
    #     limit=limit
    # )

    # print(f"Found {len(users)} users")
    # if users:
    #     pprint(users[0])

    # print("\n=== Testing AD query (computers) ===")

    # computers = active_directory_query(
    #     base_dn=base_dn,
    #     search_filter="(objectClass=computer)",
    #     limit=5
    # )

    # print(f"Found {len(computers)} computers")
    # if computers:
    #     pprint(computers[0])

    # print("\nDone.")


    pass