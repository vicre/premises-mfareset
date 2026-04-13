from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.http import HttpResponse
from premises_mfareset.utils.graph import list_user_authentication_methods
from premises_mfareset.utils.auth_methods import prepare_auth_methods
from premises_mfareset.utils.reset_mfa import reset_mfa_methods
from premises_mfareset.utils.entra_auth import (
    build_auth_url,
    acquire_token_by_auth_code,
)
import logging
import time
from django.http import JsonResponse
from django.contrib.auth.models import User


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


def auth_callback(request):
    error = request.GET.get("error")
    if error:
        return HttpResponse(
            f"{error}: {request.GET.get('error_description', 'Unknown error')}",
            status=400,
        )

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
