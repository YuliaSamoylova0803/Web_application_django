from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.checks import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.core.mail import send_mail
from .models import Recipient, Message, Mailing, MailingLog
from django.views.generic import ListView, DetailView, DeleteView
from django.views.generic.edit import CreateView, UpdateView
from .forms import RecipientForm, MessageForm, MailingForm, MailingLogForm


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
    form_class = RecipientForm
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
    form_class = RecipientForm
    template_name = "mailing_service/recipient_form.html"
    success_url = reverse_lazy("mailing_service:recipient_list")

    def get_success_url(self):
        return reverse("mailing_service:recipient_detail", args=[self.kwargs.get("pk")])


# app_name/<model_name>_action
# mailing_service/recipient_delete
class RecipientDeleteView(DeleteView):
    model = Recipient
    success_url = reverse_lazy("mailing_service:recipient_list")


class MessageListView(ListView):
    model = Message


class MessageDetailView(DetailView):
    model = Message


class MessageCreateView(CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing_service/message_form.html"
    success_url = reverse_lazy("mailing_service:message_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        response = super().form_invalid(form)
        response.context_data["error_message"] = "Please correct the errors below"

        return  response

class MessageUpdateView(UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing_service/message_form.html"
    success_url = reverse_lazy("mailing_service:message_list")

    def get_success_url(self):
        return reverse("mailing_service:message_detail", args=[self.kwargs.get("pk")])


class MessageDeleteView(DeleteView):
    model = Message
    success_url = reverse_lazy("mailing_service:message_list.html")


class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    paginate_by = 10

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class MailingDetailView(DetailView):
    model = Mailing


class MailingCreateView(CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing_service/mailing_form.html"
    success_url = reverse_lazy("mailing_service:mailing_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        response = super().form_invalid(form)
        response.context_data["error_message"] = "Please correct the errors below"

        return response


class MailingUpdateView(UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing_service/mailing_form.html"
    success_url = reverse_lazy("mailing_service:mailing_list")

    def get_success_url(self):
        return reverse("mailing_service:mailing_detail", args=[self.kwargs.get("pk")])


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    model = Mailing
    success_url = reverse_lazy("mailing_service:mailing_list")  # Убрал .html

    def form_valid(self, form):
        messages.success(self.request, "Рассылка успешно удалена")
        return super().form_valid(form)


class MailingLogListView(ListView):
    model = MailingLog


class MailingLogDetailView(DetailView):
    model = MailingLog


class MailingLogCreateView(CreateView):
    model = MailingLog
    form_class = MailingLogForm
    template_name = "mailing_service/mailing_log_form.html"
    success_url = reverse_lazy("mailing_service:mailing_log_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        response = super().form_invalid(form)
        response.context_data["error_message"] = "Please correct the errors below"

        return response


class MailingLogUpdateView(UpdateView):
    model = MailingLog
    form_class = MailingLogForm
    template_name = "mailing_service/mailing_log_form.html"
    success_url = reverse_lazy("mailing_service:mailing_log_list")

    def get_success_url(self):
        return reverse("mailing_service:mailing_log_detail", args=[self.kwargs.get("pk")])


class MailingLogDeleteView(DeleteView):
    model = MailingLog
    success_url = reverse_lazy("mailing_service:mailing_log_list.html")


def send_mailing(request, mailing_id):
    mailing = Mailing.objects.get(pk=mailing_id)
    recipients = mailing.recipients.all()
    message = mailing.message

    for recipient in recipients:
        try:
            # Отправка email
            send_mail(
                subject=message.subject_message,
                message=message.message_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )

            # Логирование успешной отправки
            MailingLog.objects.create(
                mailing=mailing,
                recipient=recipient,
                status=MailingLog.STATUS_SUCCESS,
                mail_server_response="Успешно отправлено",
            )

        except Exception as e:
            # Логирование ошибки
            MailingLog.objects.create(
                mailing=mailing,
                recipient=recipient,
                status=MailingLog.STATUS_FAILED,
                mail_server_response=str(e),
            )

    return redirect('mailing_service:mailing_detail', pk=mailing_id)
