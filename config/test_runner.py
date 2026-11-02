from contextlib import ExitStack
from unittest.mock import patch

from django.test.runner import DiscoverRunner


class OfflineTestRunner(DiscoverRunner):
    """Block network access, including import-time MSAL discovery, in tests."""

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self.offline = ExitStack()
        self.offline.enter_context(patch(
            "socket.socket.connect",
            side_effect=AssertionError("Network access is forbidden in local tests"),
        ))
        msal_app = self.offline.enter_context(patch("msal.ConfidentialClientApplication"))
        msal_app.return_value.acquire_token_for_client.return_value = {
            "access_token": "test-only-token",
        }

    def teardown_test_environment(self, **kwargs):
        self.offline.close()
        super().teardown_test_environment(**kwargs)
