from django.shortcuts import render
from django.urls import reverse_lazy, reverse

from .models import Recipient, Message, Mailing, MailingLog
from django.views.generic import ListView, DetailView, DeleteView
from django.views.generic.edit import CreateView, UpdateView

# Create your views here.
def base(request):
    return render(request, 'mailing_service/base.html')


# app_name/<model_name>_action
# mailing_service/recipient_list
class RecipientListView(ListView):
    model = Recipient


# app_name/<model_name>_action
# mailing_service/recipient_create
class RecipientCreateView(CreateView):
    model = Recipient
    fields = ["full_name", "email", "comment"]
    template_name = "mailing_service/recipient_form.html"
    success_url = reverse_lazy("mailing_service:recipient_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        response = super().form_invalid(form)
        response.context_data["error_message"] = "Please correct the errors below"

        return  response

# app_name/<model_name>_action
# mailing_service/recipient_detail
class RecipientDetailView(DetailView):
    model = Recipient


# app_name/<model_name>_action
# mailing_service/recipient_update
class RecipientUpdateView(UpdateView):
    model = Recipient
    fields = ["full_name", "email", "comment"]
    template_name = "mailing_service/recipient_form.html"
    success_url = reverse_lazy("mailing_service:recipient_list")

    def get_success_url(self):
        return reverse("mailing_service:recipient_detail", args=[self.kwargs.get("pk")])


# app_name/<model_name>_action
# mailing_service/recipient_delete
class RecipientDeleteView(DeleteView):
    model = Recipient
    success_url = reverse_lazy("mailing_service:recipient_list")