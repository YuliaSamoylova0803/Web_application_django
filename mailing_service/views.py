
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse

from .models import Recipient, Message, Mailing, MailingLog
from django.views.generic import ListView, DetailView, DeleteView, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from .forms import RecipientForm, MessageForm, MailingForm
from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache


# Create your views here.
def base(request):
    return render(request, "mailing_service/base.html")


# @method_decorator(cache_page(60 * 60), name="dispatch")
class BaseView(TemplateView):
    template_name = "mailing_service/base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Общее количество рассылок
        total_mailings = Mailing.objects.count()

        # Количество активных рассылок
        active_mailings = Mailing.objects.filter(status=Mailing.STATUS_LAUNCHED).count()

        # Количество уникальных получателей
        unique_recipients = Recipient.objects.distinct().count()

        context.update(
            {
                "total_mailings": total_mailings,
                "active_mailings": active_mailings,
                "unique_recipients": unique_recipients,
            }
        )
        return context


# app_name/<model_name>_action
# mailing_service/recipient_list
@method_decorator(cache_page(60 * 15), name="dispatch")
class RecipientListView(LoginRequiredMixin, ListView):
    model = Recipient
    template_name = "mailing_service/recipient_list.html"

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)


# app_name/<model_name>_action
# mailing_service/recipient_create


class RecipientCreateView(LoginRequiredMixin, CreateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailing_service/recipient_form.html"
    success_url = reverse_lazy("mailing_service:recipient_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Получатель успешно создан")
        return super().form_valid(form)

    def form_invalid(self, form):
        response = super().form_invalid(form)
        response.context_data["error_message"] = "Please correct the errors below"

        return response


# app_name/<model_name>_action
# mailing_service/recipient_detail
class RecipientDetailView(DetailView):
    model = Recipient


# app_name/<model_name>_action
# mailing_service/recipient_update


class RecipientUpdateView(PermissionRequiredMixin, UpdateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailing_service/recipient_form.html"
    success_url = reverse_lazy("mailing_service:recipient_list")

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)

    def get_success_url(self):
        messages.success(self.request, "Получатель успешно обновлен")
        return reverse("mailing_service:recipient_detail", args=[self.kwargs.get("pk")])

    def form_valid(self, form):
        cache.delete(f"recipient_{self.object.id}")  # Инвалидация кеша деталей
        cache.delete("recipients_list")  # Инвалидация списка
        return super().form_valid(form)


# app_name/<model_name>_action
# mailing_service/recipient_delete
class RecipientDeleteView(PermissionRequiredMixin, DeleteView):
    model = Recipient
    success_url = reverse_lazy("mailing_service:recipient_list")
    permission_required = "mailing.can_delete_own_recipient"

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Получатель успешно удален")
        return super().delete(request, *args, **kwargs)


@method_decorator(cache_page(60 * 15), name="dispatch")
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
        message = form.save()
        user = self.request.user
        message.owner = user
        message.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        response = super().form_invalid(form)
        response.context_data["error_message"] = "Please correct the errors below"

        return response


class MessageUpdateView(UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing_service/message_form.html"
    success_url = reverse_lazy("mailing_service:message_list")

    def get_success_url(self):
        return reverse("mailing_service:message_detail", args=[self.kwargs.get("pk")])


class MessageDeleteView(DeleteView):
    model = Message
    success_url = reverse_lazy("mailing_service:message_list")


@method_decorator(cache_page(60 * 15), name="dispatch")
class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "mailings/mailing_list.html"
    paginate_by = 10

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)


class MailingDetailView(DetailView):
    model = Mailing

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["logs"] = MailingLog.objects.filter(mailing=self.object)
        return context


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing_service/mailing_form.html"
    success_url = reverse_lazy("mailing_service:mailing_list")

    def get_form_kwargs(self):
        """Передаем текущего пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Автоматически назначаем владельца и показываем сообщение"""
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Рассылка успешно создана")
        return response

    def form_invalid(self, form):
        """Обработка невалидной формы с сообщением об ошибке"""
        messages.error(self.request, "Пожалуйста, исправьте ошибки в форме")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Добавляем дополнительные данные в контекст"""
        context = super().get_context_data(**kwargs)
        context["title"] = "Создание новой рассылки"
        return context


class MailingUpdateView(PermissionRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing_service/mailing_form.html"
    permission_required = "mailing.can_change_own_mailing"

    def get_queryset(self):
        """Фильтруем только рассылки текущего пользователя"""
        return Mailing.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        """Передаем текущего пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        """URL для перенаправления после успешного обновления"""
        messages.success(self.request, "Рассылка успешно обновлена")
        return reverse("mailing_service:mailing_detail", kwargs={"pk": self.object.pk})

    def form_invalid(self, form):
        """Обработка невалидной формы"""
        messages.error(self.request, "Ошибка обновления рассылки")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Добавляем дополнительные данные в контекст"""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Редактирование рассылки #{self.object.pk}"
        return context


class MailingDeleteView(PermissionRequiredMixin, DeleteView):
    model = Mailing
    success_url = reverse_lazy("mailing_service:mailing_list")
    permission_required = "mailing.can_delete_own_mailing"

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Рассылка успешно удалена")
        cache.delete("mailing_list")
        return super().delete(request, *args, **kwargs)


@method_decorator(cache_page(60 * 15), name="dispatch")
class MailingLogListView(ListView):
    model = MailingLog


class MailingLogDetailView(DetailView):
    model = MailingLog


# class MailingLogCreateView(CreateView):
#     model = MailingLog
#     form_class = MailingLogForm
#     template_name = "mailing_service/mailing_log_form.html"
#     success_url = reverse_lazy("mailing_service:mailing_log_list")
#
#     def form_valid(self, form):
#         form.instance.created_by = self.request.user
#         return super().form_valid(form)
#
#     def form_invalid(self, form):
#         response = super().form_invalid(form)
#         response.context_data["error_message"] = "Please correct the errors below"
#
#         return response
#
#
# class MailingLogUpdateView(UpdateView):
#     model = MailingLog
#     form_class = MailingLogForm
#     template_name = "mailing_service/mailing_log_form.html"
#     success_url = reverse_lazy("mailing_service:mailing_log_list")
#
#     def get_success_url(self):
#         return reverse("mailing_service:mailing_log_detail", args=[self.kwargs.get("pk")])
#
#
# class MailingLogDeleteView(DeleteView):
#     model = MailingLog
#     success_url = reverse_lazy("mailing_service:mailing_log_list")
#
#
def send_mailing(request, mailing_id):
    mailing = get_object_or_404(Mailing, pk=mailing_id)

    # Проверка прав
    if (
        not request.user.has_perm("mailing.can_start_own_mailing")
        or mailing.owner != request.user
    ):
        raise PermissionDenied

    if request.method == "POST":
        try:
            mailing.send()
            messages.success(request, "Рассылка успешно запущена")
        except Exception as e:
            messages.error(request, f"Ошибка при отправке рассылки: {str(e)}")

    return redirect("mailing_service:mailing_detail", pk=mailing_id)
