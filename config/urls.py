"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from premises_mfareset.views import (
    entra_login,
    auth_callback,
    entra_logout,
    my_mfa_admin_groups,
    reset_mfa,
    scoreboard
)


urlpatterns = [
    path('admin/', admin.site.urls),
    
    path("", my_mfa_admin_groups, name="my_mfa_admin_groups"),
    path("scoreboard/", scoreboard, name="scoreboard"),

    # This is not a site. It is a POST AJAX event that is used by it is the button that reset mfa
    path("reset-mfa/", reset_mfa, name="reset_mfa"),

    # Azure login boilerplate
    path("auth/login/", entra_login, name="entra_login"),
    path("auth/logout/", entra_logout, name="entra_logout"),
    path("auth/callback/", auth_callback, name="auth_callback"),



]

