import logging
from django.core.mail import EmailMessage

from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.conf import settings
from django.db.models import CASCADE

from users.models import User

# Настройка логгера
logger = logging.getLogger(__name__)


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

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
            if self._state.adding:
                logger.info(f"Создан новый получатель: {self.email} (ID: {self.id})")
            else:
                logger.info(f"Обновлен получатель: {self.email} (ID: {self.id})")
        except Exception as e:
            logger.error(f"Ошибка при сохранении получателя {self.email}: {str(e)}")
            raise

    def delete(self, *args, **kwargs):
        try:
            email = self.email
            super().delete(*args, **kwargs)
            logger.warning(f"Удален получатель: {email}")
        except Exception as e:
            logger.error(f"Ошибка при удалении получателя {self.email}: {str(e)}")
            raise

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
            ("can_view_all_recipients", "Can view all recipients"),
            ("can_disable_recipient", "Сan disable recipients"),
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
                                  null=True)
    owner = models.ForeignKey(User, verbose_name="Владелец", help_text="Укажите владельца сообщения",
                              blank=True, null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
            if self._state.adding:
                logger.info(f"Создано новое сообщение: '{self.subject_message}' (ID: {self.id})")
            else:
                logger.info(f"Обновлено сообщение: '{self.subject_message}' (ID: {self.id})")
        except Exception as e:
            logger.error(f"Ошибка при сохранении сообщения '{self.subject_message}': {str(e)}")
            raise

    def delete(self, *args, **kwargs):
        try:
            subject = self.subject_message
            super().delete(*args, **kwargs)
            logger.warning(f"Удалено сообщение: '{subject}'")
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения '{self.subject_message}': {str(e)}")
            raise

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
            ("can_view_all_messages", "Can view all messages"),
            ("can_send_message", "Can send messages manually"),
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

    def clean(self):
        if self.end_shipment <= self.first_shipment:
            error_msg = "Дата окончания должна быть позже даты начала"
            logger.error(f"Ошибка валидации рассылки {self.id}: {error_msg}")
            raise ValidationError(error_msg)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
            if self._state.adding:
                logger.info(f"Создана новая рассылка ID {self.id} (Статус: {self.get_status_display()})")
            else:
                logger.info(f"Обновлена рассылка ID {self.id} (Статус: {self.get_status_display()})")
        except Exception as e:
            logger.error(f"Ошибка при сохранении рассылки {self.id}: {str(e)}")
            raise

    def delete(self, *args, **kwargs):
        try:
            mailing_id = self.id
            super().delete(*args, **kwargs)
            logger.warning(f"Удалена рассылка ID {mailing_id}")
        except Exception as e:
            logger.error(f"Ошибка при удалении рассылки {self.id}: {str(e)}")
            raise

    def send(self):
        logger.info(f"Запуск рассылки ID {self.id} для {self.recipients.count()} получателей")

        success_count = 0
        fail_count = 0

        for recipient in self.recipients.all():
            try:
                # Используем EmailMessage из django.core.mail
                from django.core.mail import EmailMessage
                import os

                email = EmailMessage(
                    subject=self.message.subject_message,
                    body=self.message.message_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient.email],
                )

                # Обработка вложения с определением MIME-типа
                if self.message.attachment:
                    filename = os.path.basename(self.message.attachment.path)
                    content_type = 'application/octet-stream'

                    # Определяем Content-Type по расширению файла
                    if filename.lower().endswith(('.jpg', '.jpeg')):
                        content_type = 'image/jpeg'
                    elif filename.lower().endswith('.png'):
                        content_type = 'image/png'
                    elif filename.lower().endswith('.pdf'):
                        content_type = 'application/pdf'
                    elif filename.lower().endswith(('.doc', '.docx')):
                        content_type = 'application/msword'
                    elif filename.lower().endswith('.xlsx'):
                        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

                    # Читаем файл и прикрепляем
                    with open(self.message.attachment.path, 'rb') as file:
                        email.attach(
                            filename=filename,
                            content=file.read(),
                            mimetype=content_type
                        )

                email.send()
                success_count += 1

                MailingLog.objects.create(
                    mailing=self,
                    recipient=recipient,
                    status=MailingLog.STATUS_SUCCESS,
                    mail_server_response="Успешно отправлено",
                )
                logger.debug(f"Письмо успешно отправлено для {recipient.email}")

            except Exception as e:
                fail_count += 1
                error_msg = str(e)
                logger.error(f"Ошибка отправки для {recipient.email}: {error_msg}")

                MailingLog.objects.create(
                    mailing=self,
                    recipient=recipient,
                    status=MailingLog.STATUS_FAILED,
                    mail_server_response=error_msg,
                )

        logger.info(
            f"Рассылка ID {self.id} завершена. "
            f"Успешно: {success_count}, Неудачно: {fail_count}"
        )
        self.status = self.STATUS_LAUNCHED
        self.save()

    class Meta:
        verbose_name = "рассылка"
        verbose_name_plural = "рассылки"
        ordering = ["-first_shipment", "status"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["first_shipment"]),
            models.Index(fields=["is_active"]),
        ]
        permissions = [
            ("can_view_all_mailing", "Can view all mailings"),
            ("can_change_own_mailing", "Can change own mailings"),
            ("can_delete_own_mailing", "Can delete own mailings"),
            ("can_disable_mailing", "Может отключать любые рассылки"),
            ("can_start_mailing", "Может запускать любые рассылки"),
        ]

    def __str__(self):
        return f"Рассылка #{self.id} ({self.get_status_display() or 'Без статуса'})"


class MailingLog(models.Model):
    """
    Модель попытки рассылки.
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
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Владелец")

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
            logger.debug(
                f"Записана попытка рассылки для рассылки ID {self.mailing_id}. "
                f"Статус: {self.get_status_display()}"
            )
        except Exception as e:
            logger.error(f"Ошибка при сохранении лога рассылки: {str(e)}")
            raise

    class Meta:
        verbose_name = "попытка рассылки"
        verbose_name_plural = "попытки рассылки"
        ordering = ["-date_of_attempt"]
        indexes = [
            models.Index(fields=["status", "owner"]),
            models.Index(fields=["date_of_attempt"]),
        ]
        permissions = [
            ("can_view_all_logs", "Can view all logs"),
            ("can_delete_logs", "Can delete logs"),
        ]

    def __str__(self):
        return f"Попытка #{self.id} ({self.get_status_display()}) для {self.mailing} - {self.recipient}"