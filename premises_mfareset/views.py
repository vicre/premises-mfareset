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

logger = logging.getLogger(__name__)


def home(request):
    return render(request, "core/home.html")


@login_required
def profile(request):
    attributes = request.session.get("attributes", {})
    auth_methods = []
    graph_error = None

    try:
        username = request.user.username.strip().lower()
        if "@" not in username:
            username = f"{username}@dtu.dk"

        raw_methods = list_user_authentication_methods(username)
        auth_methods = prepare_auth_methods(raw_methods)
    except Exception:
        logger.exception("Failed to fetch authentication methods for %s", username)
        graph_error = "Could not retrieve authentication methods at the moment."

    return render(
        request,
        "core/profile.html",
        {
            "cas_attributes": attributes,
            "resolved_upn": username,
            "auth_methods": auth_methods,
            "graph_error": graph_error,
        },
    )


@login_required
def reset_mfa(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        username = request.user.username.strip().lower()
        if "@" not in username:
            username = f"{username}@dtu.dk"
        methods = list_user_authentication_methods(username)
        mfa_methods = prepare_auth_methods(methods)

        message = reset_mfa_methods(username, mfa_methods)

        return JsonResponse({
            "success": True,
            "message": message,
        }, status=200)

    except Exception as exc:
        return JsonResponse({
            "success": False,
            "message": str(exc),
        }, status=500)




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
    
    #                                               #
    ####### Check if user is synched with AD ########
    #                                               #
    #
    # Get get user from Azure, with the on_premises_immutable_id property
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
    #
    #
    if not is_synced:
        return HttpResponse("User is not synced with on-prem AD", status=403)
    #
    ####### Ends here ########




    #                                                                                                                               #
    ####### Check if user is member of any groups under OU=MFAResetAdmins,OU=Groups,OU=SOC,OU=CIS,OU=AIT,DC=win,DC=dtu,DC=dk ########
    #                                                                                                                               #
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
    return redirect("profile")


@login_required
def profile(request):
    return render(
        request,
        "core/profile.html",
        {"claims": request.session.get("entra_claims", {})},
    )


def entra_logout(request):
    logout(request)
    return redirect("home")
