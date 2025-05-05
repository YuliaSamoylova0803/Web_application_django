from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from users.apps import UsersConfig

app_name = UsersConfig.name

urlpatterns =[
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),  # надо поменять на home
    path("logout/", LogoutView.as_view(next_page="mailing_service:base"), name="logout"),





]