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


    pass