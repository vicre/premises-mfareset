from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.http import HttpResponse
from active_directory.utils.user_is_member_of_admin_group_in_ad import user_is_member_of_admin_group_in_ad
from premises_mfareset.utils.graph import list_user_authentication_methods
from premises_mfareset.utils.auth_methods import prepare_auth_methods
from premises_mfareset.utils.reset_mfa import reset_mfa_methods
from premises_mfareset.utils.entra_auth import (
    build_auth_url,
    acquire_token_by_auth_code,
)
import logging
from django.http import JsonResponse
from django.contrib.auth.models import User
from active_directory.utils.azure_user_is_synced_with_on_premise_user import (
    azure_user_is_synced_with_on_premise_user,
)
from premises_mfareset.utils.graph import get_user
from active_directory.utils.active_directory_query import active_directory_query
from active_directory.utils.get_user_mfa_admin_groups import get_user_mfa_admin_groups



logger = logging.getLogger(__name__)

def _normalize_upn(value: str) -> str:
    value = (value or "").strip().lower()
    if value and "@" not in value:
        value = f"{value}@dtu.dk"
    return value


def _extract_allowed_ous(groups: list[dict]) -> list[str]:
    allowed_ous = []

    for group in groups:
        ea_list = group.get("extensionAttribute1", [])
        if not ea_list:
            continue

        ea_value = ea_list[0]
        for ou in ea_value.split(","):
            ou = ou.strip().upper()
            if ou and ou not in allowed_ous:
                allowed_ous.append(ou)

    return allowed_ous


def _get_target_user_from_ad(target_upn: str) -> dict | None:
    target_users = active_directory_query(
        base_dn="DC=win,DC=dtu,DC=dk",
        search_filter=f"(&(objectClass=user)(userPrincipalName={target_upn}))",
        search_attributes=[
            "cn",
            "displayName",
            "mail",
            "userPrincipalName",
            "distinguishedName",
            "sAMAccountName",
        ],
        limit=1,
    )

    if not target_users:
        return None

    entry = target_users[0]

    return {
        "cn": entry.get("cn", [""])[0],
        "display_name": entry.get("displayName", [""])[0] if entry.get("displayName") else "",
        "mail": entry.get("mail", [""])[0] if entry.get("mail") else "",
        "user_principal_name": entry.get("userPrincipalName", [""])[0] if entry.get("userPrincipalName") else target_upn,
        "distinguished_name": entry.get("distinguishedName", [""])[0] if entry.get("distinguishedName") else "",
        "sam_account_name": entry.get("sAMAccountName", [""])[0] if entry.get("sAMAccountName") else "",
    }


def _get_target_ou_from_dn(distinguished_name: str) -> str | None:
    """
    Expected:
      CN=testtes,OU=AIT,OU=DTUBaseUsers,DC=win,DC=dtu,DC=dk

    Returns:
      AIT
    """
    if not distinguished_name:
        return None

    dn_parts = [part.strip() for part in distinguished_name.split(",")]

    for i, part in enumerate(dn_parts):
        if part.upper() == "OU=DTUBASEUSERS":
            if i > 0 and dn_parts[i - 1].upper().startswith("OU="):
                return dn_parts[i - 1][3:].upper()
            return None

    return None




@login_required
def my_mfa_admin_groups(request):
    admin_upn = _normalize_upn(request.user.username)

    raw_groups = get_user_mfa_admin_groups(admin_upn)
    allowed_ous = _extract_allowed_ous(raw_groups)

    groups = []
    for group in raw_groups:
        ea_value = group.get("extensionAttribute1", [""])[0] if group.get("extensionAttribute1") else ""
        groups.append({
            "cn": group.get("cn", [""])[0],
            "description": group.get("description", [""])[0] if group.get("description") else "",
            "distinguished_name": group.get("distinguishedName", [""])[0] if group.get("distinguishedName") else "",
            "extension_attribute_1": ea_value,
            "scopes": [item.strip() for item in ea_value.split(",") if item.strip()],
        })

    target_upn = _normalize_upn(request.GET.get("target_upn", ""))
    target_user = None
    target_ou = None
    is_allowed = False

    if target_upn:
        target_user = _get_target_user_from_ad(target_upn)
        if target_user:
            target_ou = _get_target_ou_from_dn(target_user["distinguished_name"])
            if target_ou and target_ou in allowed_ous:
                is_allowed = True

    return render(
        request,
        "premises_mfareset/my_mfa_admin_groups.html",
        {
            "admin_upn": admin_upn,
            "groups": groups,
            "allowed_ous": allowed_ous,
            "target_upn": target_upn,
            "target_user": target_user,
            "target_ou": target_ou,
            "is_allowed": is_allowed,
        },
    )

@login_required
def scoreboard(request):
    return render(request, "premises_mfareset/scoreboard.html")

@login_required
def reset_mfa(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        admin_upn = _normalize_upn(request.user.username)
        target_upn = _normalize_upn(request.POST.get("target_upn", ""))

        if not target_upn:
            return JsonResponse(
                {"success": False, "message": "Missing target_upn"},
                status=400,
            )

        raw_groups = get_user_mfa_admin_groups(admin_upn)
        allowed_ous = _extract_allowed_ous(raw_groups)

        if not allowed_ous:
            return JsonResponse(
                {"success": False, "message": "You are not allowed to reset MFA for any OU"},
                status=403,
            )

        target_user = _get_target_user_from_ad(target_upn)
        if not target_user:
            return JsonResponse(
                {"success": False, "message": f"Target user not found: {target_upn}"},
                status=404,
            )

        target_ou = _get_target_ou_from_dn(target_user["distinguished_name"])
        if not target_ou:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Target user is not under OU=DTUBaseUsers/<OU>/...",
                },
                status=403,
            )

        if target_ou not in allowed_ous:
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        f"Not allowed. Target user is in OU '{target_ou}', "
                        f"allowed OUs are: {', '.join(allowed_ous)}"
                    ),
                },
                status=403,
            )

        methods = list_user_authentication_methods(target_upn)
        mfa_methods = prepare_auth_methods(methods)
        message = reset_mfa_methods(target_upn, mfa_methods)

        return JsonResponse(
            {
                "success": True,
                "message": message,
                "target_upn": target_upn,
                "target_ou": target_ou,
            },
            status=200,
        )

    except Exception as exc:
        return JsonResponse(
            {"success": False, "message": str(exc)},
            status=500,
        )



### Azure login starter her ###
def entra_login(request):
    return redirect(build_auth_url())

# The user is allowed to pass if:
# 1. authorazition code is OK
# 2. if user is synched with AD
# 3. if user is member of any of the MFAResetAdmins groups in AD
def auth_callback(request):
    
    # Check if the callback contains an error
    error = request.GET.get("error")
    if error:
        return HttpResponse(
            f"{error}: {request.GET.get('error_description', 'Unknown error')}",
            status=400,
        )
    
    # Get the authorazition code from the url
    code = request.GET.get("code")
    if not code:
        return HttpResponse("Missing authorization code", status=400)

    result = acquire_token_by_auth_code(code)

    if "access_token" not in result:
        return HttpResponse(
            f"{result.get('error')}: {result.get('error_description')}",
            status=400,
        )

    claims = result.get("id_token_claims", {})
    username = (
        claims.get("preferred_username")
        or claims.get("upn")
        or claims.get("sub")
    )
    email = claims.get("email") or claims.get("preferred_username") or ""

    # Check if user is synched with AD
    select_param = "$select=onPremisesImmutableId"
    try:
        response = get_user(
            user_principal_name=email,
            select_parameters=select_param,
        )
    except Exception as error:
        print("User not found in Azure")
        print("Error:", error)
        return

    on_premises_immutable_id = response.get("onPremisesImmutableId")
    is_synced = azure_user_is_synced_with_on_premise_user(
        user_principal_name=email,
        on_premises_immutable_id=on_premises_immutable_id,
    )

    if not is_synced:
        return HttpResponse("User is not synced with on-prem AD", status=403)

    # Check if user is member of any groups under OU=MFAResetAdmins,OU=Groups,OU=SOC,OU=CIS,OU=AIT,DC=win,DC=dtu,DC=dk                                                                                                                              #
    user_is_member_of_mfa_reset_group = user_is_member_of_admin_group_in_ad(email)
    
    if not user_is_member_of_mfa_reset_group:
        return HttpResponse("User is not member of MFA reset group", status=403)

    user, _ = User.objects.get_or_create(
        username=username,
        defaults={"email": email},
    )

    login(request, user)
    request.session["entra_claims"] = claims
    request.session["access_token"] = result.get("access_token")
    return redirect("home")


def entra_logout(request):
    logout(request)
    return redirect("home")

### Azure login starter her ###