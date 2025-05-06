from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, \
    PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import path
import uuid

from users.apps import UsersConfig
from users.views import RegisterView, email_verification

app_name = UsersConfig.name

urlpatterns =[
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),  # надо поменять на home
    path("logout/", LogoutView.as_view(next_page="mailing_service:base"), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("email_confirm/<str:token>/", email_verification, name="email_confirm"),

    path("password_reset/", PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", PasswordResetCompleteView.as_view(), name="password_reset_complete"),

]