from django.contrib import admin

from .models import Recipient, Message, MailingLog, Mailing

# Register your models here.
@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "email", "comment", "created_at")
    list_filter = ("id", "email", "full_name")
    search_fields = ("email", "comment", "full_name",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "subject_message", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("message_body", "subject_message",)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "status", "is_active", "first_shipment", "end_shipment")
    list_filter = ("status", "is_active", "first_shipment")
    search_fields = ("message__subject_message", "status")
    filter_horizontal = ("recipients",)  # Для удобного выбора получателей
    date_hierarchy = "first_shipment"  # Иерархия по дате


@admin.register(MailingLog)
class MailingLogAdmin(admin.ModelAdmin):
    list_display = ("id", "mailing", "recipient", "status", "date_of_attempt")
    list_filter = ("status", "date_of_attempt", "mailing")
    search_fields = ("mail_server_response", "recipient__email")
