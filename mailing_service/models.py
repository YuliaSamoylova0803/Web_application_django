from email.message import EmailMessage

from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.conf import settings
from django.db.models import CASCADE

from users.models import User


# Create your models here.
class Recipient(models.Model):
    """
    Модель получателя рассылки.
    Содержит контактные данные и информацию о получателе.
    """
    email = models.EmailField(max_length=50, unique=True, verbose_name="Почта",
                              help_text="Введите свою электронную почту")
    full_name = models.CharField(max_length=100, verbose_name="ФИО получателя", help_text="Введите Ф.И.О.")
    comment = models.TextField(verbose_name="Комментарий", blank=True, help_text="Дополнительные данные")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    owner = models.ForeignKey(User, verbose_name="Владелец", blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "получатель"
        verbose_name_plural = "получатели"
        ordering = ["full_name", "email"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["full_name"]),
        ]
        permissions = [
            ("can_view_own_recipient", "Can view own recipients"),
            ("can_change_own_recipient", "Can change own recipients"),
            ("can_delete_own_recipient", "Can delete own recipients"),
        ]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class Message(models.Model):
    """
       Модель сообщения для рассылки.
       Содержит тему, текст и возможные вложения.
       """
    subject_message = models.CharField(max_length=255, verbose_name="Тема письма", help_text="Какова тема письма?",
                                       validators=[
                                           MinLengthValidator(5),
                                           MaxLengthValidator(100),
                                       ])
    message_body = models.TextField(verbose_name="Тело сообщения", help_text="Введите сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    attachment = models.FileField(upload_to="message_attachments/%Y/%m/%d/", verbose_name="Вложение", blank=True,
                                  null=True, )

    owner = models.ForeignKey(User, verbose_name="Владелец", help_text="Укажите владельца сообщения", blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "сообщение"
        verbose_name_plural = "сообщения"
        ordering = ["-created_at", "subject_message"]
        indexes = [
            models.Index(fields=["subject_message"]),
        ]
        permissions = [
            ("can_view_own_message", "Can view own messages"),
            ("can_change_own_message", "Can change own messages"),
            ("can_delete_own_messages", "Can delete own messages"),
        ]

    def __str__(self):
        return self.subject_message


class Mailing(models.Model):
    """
        Модель рассылки сообщений.
        Определяет параметры и статус рассылки.
        """
    first_shipment = models.DateTimeField(verbose_name="Дата и время первой отправки",
                                          help_text="Дата и время первой отправки")
    end_shipment = models.DateTimeField(verbose_name="Дата и время окончания отправки",
                                        help_text="Дата и время окончания отправки")
    STATUS_CREATED = "CREATED"
    STATUS_LAUNCHED = "LAUNCHED"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CHOICES = (
        (None, "Выберите статус рассылки"),
        (STATUS_CREATED, "Создана"),
        (STATUS_LAUNCHED, "Запущена"),
        (STATUS_COMPLETED, "Завершена"),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, verbose_name="Статус",
                              help_text="Выберите статус рассылки")
    message = models.ForeignKey(Message, on_delete=CASCADE, verbose_name="Cообщения", related_name="messages")
    recipients = models.ManyToManyField(Recipient, verbose_name="Получатели")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_active = models.BooleanField(default=True, verbose_name="Активна", help_text="Указывает, активна ли рассылка")

    owner = models.ForeignKey(User, verbose_name="Владелец", help_text="Укажите владельца рассылки", blank=True,
                              null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "рассылка"
        verbose_name_plural = "рассылки"
        ordering = ["-first_shipment", "status", ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["first_shipment"]),
            models.Index(fields=["is_active"]),
        ]
        permissions = [
            ("can_view_own_mailing", "Can view own mailings"),
            ("can_change_own_mailing", "Can change own mailings"),
            ("can_delete_own_mailing", "Can delete own mailings"),
            ("can_start_own_mailing", "Can start own mailings"),
        ]

    def __str__(self):
        return f"Рассылка #{self.id} ({self.get_status_display() or 'Без статуса'})"


    def send(self):
        from django.core.mail import send_mail
        from django.conf import settings

        for recipient in self.recipients.all():
            try:
                email= EmailMessage(
                    subject=self.message.subject_message,
                    body=self.message.message_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient.email],
                )
                if self.message.attachment:
                    email.attach_file(self.message.attachment.path)

                email.send()

                MailingLog.objects.create(
                    mailing=self,
                    recipient=recipient,
                    status=MailingLog.STATUS_SUCCESS,
                    mail_server_response="Успешно отправлено",
                )

            except Exception as e:
                MailingLog.objects.create(
                    mailing=self,
                    recipient=recipient,
                    status=MailingLog.STATUS_FAILED,
                    mail_server_response=str(e),
                )

        self.status = self.STATUS_LAUNCHED
        self.save()


class MailingLog(models.Model):
    """
        Модель попытка рассылки.
        Фиксирует результаты отправки сообщений.
        """
    date_of_attempt = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")

    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Успешно"),
        (STATUS_FAILED, "Не успешно"),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name="Статус")
    mail_server_response = models.TextField(verbose_name="Ответ почтового сервера")
    mailing = models.ForeignKey(Mailing, on_delete=CASCADE, verbose_name="Рассылка")
    recipient = models.ForeignKey(Recipient, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name="Получатель")

    class Meta:
        verbose_name = "попытка рассылки"
        verbose_name_plural = "попытки рассылки"
        ordering = ["-date_of_attempt"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["date_of_attempt"]),
        ]

    def __str__(self):
        return f"Попытка #{self.id} ({self.get_status_display()}) для {self.mailing} - {self.recipient}"
