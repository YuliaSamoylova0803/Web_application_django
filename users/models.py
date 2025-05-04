from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name="Email")

    phone = models.CharField(max_length=35, verbose_name="Телефон", blank=True, null=True, help_text="Введите номер телефона")
    tg_nick = models.CharField(max_length=50, verbose_name="Ник телеграмм", blank=True, null=True, help_text="Введите ник телеграмм")
    avatar = models.ImageField(upload_to="users/avatars/", verbose_name="Аватарка", blank=True, null=True, help_text="Загрузите свою аватарку")
    country = models.CharField(max_length=50, blank=True, null=True, help_text="Введите страну проживания")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email
