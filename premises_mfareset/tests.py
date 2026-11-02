from copy import deepcopy
from html.parser import HTMLParser
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, SimpleTestCase, TestCase

from premises_mfareset.models import MfaResetAuditLog
from premises_mfareset.utils.auth_methods import prepare_auth_methods
from premises_mfareset.utils.graph import delete_user_authentication_method
from premises_mfareset.utils.reset_mfa import reset_mfa_methods


FIDO2 = "#microsoft.graph.fido2AuthenticationMethod"
TARGET = "sample.user@example.com"
METHODS = [
    {"id": "phone", "@odata.type": "#microsoft.graph.phoneAuthenticationMethod"},
    {"id": "authenticator", "@odata.type": "#microsoft.graph.microsoftAuthenticatorAuthenticationMethod"},
    {"id": "oath", "@odata.type": "#microsoft.graph.softwareOathAuthenticationMethod"},
    {"id": "passkey-phone", "@odata.type": FIDO2, "displayName": "Sample phone", "model": "Authenticator"},
    {"id": "passkey-key", "@odata.type": FIDO2, "displayName": "Sample security key"},
    {"id": "password", "@odata.type": "#microsoft.graph.passwordAuthenticationMethod"},
    {"id": "hello", "@odata.type": "#microsoft.graph.windowsHelloForBusinessAuthenticationMethod"},
]


class InputParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.inputs = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            self.inputs.append(dict(attrs))


class MethodTests(SimpleTestCase):
    def test_default_selection_preserves_passkeys_for_existing_script_callers(self):
        methods = prepare_auth_methods(METHODS)
        self.assertEqual({m["id"] for m in methods}, {"phone", "authenticator", "oath"})

    def test_fido2_is_labeled_and_password_and_hello_remain_excluded(self):
        methods = prepare_auth_methods(METHODS, include_fido2=True)
        self.assertEqual({m["id"] for m in methods}, {
            "phone", "authenticator", "oath", "passkey-phone", "passkey-key",
        })
        passkey = next(m for m in methods if m["id"] == "passkey-phone")
        self.assertEqual(passkey["label"], "Passkey / FIDO2 security key")
        self.assertEqual(passkey["details"], "Sample phone (Authenticator)")
        self.assertTrue(passkey["can_delete"])

    def test_unnamed_passkey_has_a_readable_fallback(self):
        methods = prepare_auth_methods([{"id": "key", "@odata.type": FIDO2}], include_fido2=True)
        self.assertEqual([m["details"] for m in methods], ["Unnamed passkey"])

    def test_fido2_delete_uses_stable_endpoint_without_body(self):
        with patch("premises_mfareset.utils.graph.requests.delete", return_value=SimpleNamespace(status_code=204)) as delete:
            try:
                delete_user_authentication_method(TARGET, "passkey-key", FIDO2)
            except ValueError as exc:
                self.fail(str(exc))
        self.assertEqual(delete.call_args.args, (
            "https://graph.microsoft.com/v1.0/users/sample.user@example.com/authentication/fido2Methods/passkey-key",
        ))
        self.assertNotIn("json", delete.call_args.kwargs)
        self.assertNotIn("data", delete.call_args.kwargs)

    def test_unknown_methods_cannot_be_deleted(self):
        with patch("premises_mfareset.utils.graph.requests.delete") as delete:
            for method_type in ["#microsoft.graph.passwordAuthenticationMethod", "#microsoft.graph.windowsHelloForBusinessAuthenticationMethod", "unknown"]:
                with self.subTest(method_type=method_type), self.assertRaises(ValueError):
                    delete_user_authentication_method(TARGET, "id", method_type)
            delete.assert_not_called()

    def test_verification_checks_raw_ids_even_if_method_type_is_unrecognized(self):
        with patch("premises_mfareset.utils.reset_mfa.delete_user_authentication_method"), patch(
            "premises_mfareset.utils.reset_mfa.list_user_authentication_methods",
            return_value=[{"id": "passkey-key", "@odata.type": "unknown"}],
        ):
            with self.assertRaisesRegex(RuntimeError, "still appears present"):
                reset_mfa_methods(TARGET, [{"id": "passkey-key", "type": FIDO2}], verify_retries=1, verify_delay_seconds=0)

    def test_verification_waits_until_fido2_is_absent(self):
        with patch("premises_mfareset.utils.reset_mfa.delete_user_authentication_method"), patch(
            "premises_mfareset.utils.reset_mfa.list_user_authentication_methods",
            side_effect=[[{"id": "passkey-key", "@odata.type": FIDO2}], []],
        ) as fetch:
            result = reset_mfa_methods(TARGET, [{"id": "passkey-key", "type": FIDO2}], verify_retries=2, verify_delay_seconds=0)
        self.assertEqual(result, "MFA methods successfully reset.")
        self.assertEqual(fetch.call_count, 2)


class ResetTests(TestCase):
    def setUp(self):
        self.actor = User.objects.create_user(username="sample.operator@example.com")
        self.client.force_login(self.actor)
        self.methods = deepcopy(METHODS)
        self.deleted_urls = []
        self.groups = self.enterContext(patch(
            "premises_mfareset.views.get_user_mfa_admin_groups",
            return_value=[{"cn": ["Sample MFA admins"], "extensionAttribute1": ["AIT"]}],
        ))
        self.target = self.enterContext(patch(
            "premises_mfareset.views._get_target_user_from_ad",
            return_value={
                "cn": "Sample User", "display_name": "Sample User", "user_principal_name": TARGET,
                "distinguished_name": "CN=Sample,OU=AIT,OU=DTUBaseUsers,DC=win,DC=dtu,DC=dk",
            },
        ))
        self.graph_get = self.enterContext(patch(
            "premises_mfareset.utils.graph.graph_get",
            side_effect=lambda url: {"value": deepcopy(self.methods)},
        ))
        self.delete = self.enterContext(patch(
            "premises_mfareset.utils.graph.requests.delete", side_effect=self.delete_method,
        ))

    def delete_method(self, url, **kwargs):
        self.deleted_urls.append(url)
        method_id = url.rsplit("/", 1)[1]
        self.methods = [m for m in self.methods if m["id"] != method_id]
        return SimpleNamespace(status_code=204)

    def reset(self, **kwargs):
        return self.client.post("/reset-mfa/", {"target_upn": TARGET, **kwargs})

    def test_unchecked_reset_preserves_all_passkeys(self):
        response = self.reset()
        self.assertEqual(response.status_code, 200)
        self.assertEqual({m["id"] for m in self.methods}, {"passkey-phone", "passkey-key", "password", "hello"})
        audit = MfaResetAuditLog.objects.latest("pk")
        self.assertEqual({m["id"] for m in audit.prepared_methods_payload}, {"phone", "authenticator", "oath"})
        self.assertIs(audit.reset_result_payload.get("include_fido2"), False)

    def test_checked_reset_deletes_all_passkeys_and_audits_scope(self):
        response = self.reset(include_fido2="1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual({m["id"] for m in self.methods}, {"password", "hello"})
        self.assertEqual(sum("/fido2Methods/" in url for url in self.deleted_urls), 2)
        audit = MfaResetAuditLog.objects.latest("pk")
        self.assertTrue(audit.success)
        self.assertIs(audit.reset_result_payload.get("include_fido2"), True)
        refreshed = self.client.get("/", {"target_upn": TARGET})
        self.assertContains(refreshed, "MFA methods successfully reset.")
        self.assertContains(refreshed, "0 passkeys")
        self.assertNotContains(refreshed, "Sample phone")

    def test_other_values_do_not_enable_passkey_deletion(self):
        for value in ["0", "true", "on", "", "yes"]:
            with self.subTest(value=value):
                self.methods = deepcopy(METHODS)
                self.deleted_urls.clear()
                self.assertEqual(self.reset(include_fido2=value).status_code, 200)
                self.assertFalse(any("/fido2Methods/" in url for url in self.deleted_urls))

    def test_passkey_only_user_is_unchanged_without_opt_in(self):
        self.methods = [deepcopy(METHODS[3])]
        response = self.reset()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "No MFA methods to delete.")
        self.delete.assert_not_called()

    def test_passkey_only_user_can_be_reset_with_opt_in(self):
        self.methods = [deepcopy(METHODS[3])]
        self.assertEqual(self.reset(include_fido2="1").status_code, 200)
        self.assertEqual(self.methods, [])

    def test_opt_in_does_not_bypass_target_ou_authorization(self):
        self.target.return_value["distinguished_name"] = "CN=Sample,OU=OTHER,OU=DTUBaseUsers,DC=win,DC=dtu,DC=dk"
        self.assertEqual(self.reset(include_fido2="1").status_code, 403)
        self.graph_get.assert_not_called()
        self.delete.assert_not_called()

    def test_operator_without_admin_group_cannot_delete(self):
        self.groups.return_value = []
        self.assertEqual(self.reset(include_fido2="1").status_code, 403)
        self.delete.assert_not_called()

    def test_anonymous_user_cannot_delete(self):
        self.client.logout()
        self.assertEqual(self.reset(include_fido2="1").status_code, 302)
        self.delete.assert_not_called()

    def test_csrf_is_still_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.actor)
        response = client.post("/reset-mfa/", {"target_upn": TARGET, "include_fido2": "1"})
        self.assertEqual(response.status_code, 403)
        self.delete.assert_not_called()

    def test_graph_failure_is_reported_and_audited(self):
        self.methods = [deepcopy(METHODS[3])]
        self.delete.side_effect = None
        self.delete.return_value = SimpleNamespace(status_code=403, text="Denied by Graph")
        response = self.reset(include_fido2="1")
        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.json()["success"])
        audit = MfaResetAuditLog.objects.latest("pk")
        self.assertFalse(audit.success)
        self.assertIn("Graph DELETE failed: 403", audit.message)
        self.assertIs(audit.reset_result_payload.get("include_fido2"), True)

    def test_checkbox_is_unchecked_and_explains_scope(self):
        response = self.client.get("/", {"target_upn": TARGET})
        self.assertEqual(response.status_code, 200)
        inputs = InputParser(response.content.decode()).inputs
        controls = [item for item in inputs if item.get("name") == "include_fido2"]
        self.assertEqual(len(controls), 1)
        self.assertEqual(controls[0]["type"], "checkbox")
        self.assertEqual(controls[0]["value"], "1")
        self.assertNotIn("checked", controls[0])
        self.assertContains(response, 'for="include_fido2"')
        self.assertContains(response, "Slet også passkeys / FIDO2-sikkerhedsnøgler")
        self.assertContains(response, "2 passkeys")
        self.assertContains(response, "bevares")

    def test_unauthorized_page_has_no_passkey_delete_control(self):
        self.groups.return_value = []
        response = self.client.get("/", {"target_upn": TARGET})
        self.assertNotContains(response, 'name="include_fido2"')

    def test_reset_confirmation_is_an_initially_closed_in_page_dialog(self):
        response = self.client.get("/", {"target_upn": TARGET})
        self.assertContains(response, '<dialog id="reset-confirmation"')
        self.assertNotContains(response, '<dialog id="reset-confirmation" open')
        self.assertContains(response, 'id="confirm-reset"')
        self.assertContains(response, 'id="cancel-reset"')
