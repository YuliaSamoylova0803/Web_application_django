from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name="Email")

    phone = models.CharField(
        max_length=35,
        verbose_name="Телефон",
        blank=True,
        null=True,
        help_text="Введите номер телефона",
    )
    tg_nick = models.CharField(
        max_length=50,
        verbose_name="Ник телеграмм",
        blank=True,
        null=True,
        help_text="Введите ник телеграмм",
    )
    avatar = models.ImageField(
        upload_to="users/avatars/",
        verbose_name="Аватарка",
        blank=True,
        null=True,
        help_text="Загрузите свою аватарку",
    )
    country = models.CharField(
        max_length=50, blank=True, null=True, help_text="Введите страну проживания"
    )

    token = models.CharField(
        max_length=100, verbose_name="Token", blank=True, null=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        permissions = [
            ("can_view_user_list", "Может просматривать список пользователей"),
            ("can_block_user", "Может блокировать пользователей (is_active=False)"),
            (
                "can_view_all_users",
                "Может просматривать всех пользователей (не только своих)",
            ),
        ]

    def __str__(self):
        return self.email
