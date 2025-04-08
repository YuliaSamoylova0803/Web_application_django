from django.urls import path

from .views import base
from mailing_service.apps import MailingServiceConfig

app_name = MailingServiceConfig.name

urlpatterns =[
    path("", base, name="base"),
]