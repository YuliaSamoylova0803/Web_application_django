from django.urls import path

from .views import base
from mailing_service.apps import MailingServiceConfig
from .views import RecipientCreateView, RecipientListView, RecipientDetailView, RecipientUpdateView, RecipientDeleteView

app_name = MailingServiceConfig.name

urlpatterns =[
    path("", base, name="base"),  # надо поменять на home
    path("recipients/", RecipientListView.as_view(), name="recipient_list"),
    path("recipients/new/", RecipientCreateView.as_view(), name="recipient_create"),
    path("recipients/<int:pk>/", RecipientDetailView.as_view(), name="recipient_detail"),
    path("recipients/<int:pk>/update/", RecipientUpdateView.as_view(), name="recipient_update"),
    path("recipients/<int:pk>/delete/", RecipientDeleteView.as_view(), name="recipient_delete")

]