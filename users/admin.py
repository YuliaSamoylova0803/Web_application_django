from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


# Register your models here.


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "phone", "country", "avatar", "tg_nick")
