from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from users.models import User
from mailing_service.models import Recipient, Message, Mailing, MailingLog


class Command(BaseCommand):
    help = 'Создает группу "Менеджер" с полным набором прав для управления сервисом'

    def handle(self, *args, **options):
        # Создаем или получаем группу
        group, created = Group.objects.get_or_create(name="Менеджер")

        if created:
            self.stdout.write(self.style.SUCCESS('Группа "Менеджер" создана'))
        else:
            self.stdout.write(self.style.WARNING('Группа "Менеджер" уже существует, обновляем права'))

        # Собираем все необходимые права
        permissions_to_add = []

        # 1. Права для работы с пользователями
        permissions_to_add.extend([
            'view_user',  # Просмотр пользователей
            'change_user',  # Блокировка (через is_active)
        ])

        # 2. Права для работы с получателями (Recipient)
        permissions_to_add.extend([
            'can_view_all_recipients',  # Просмотр всех клиентов
            'can_disable_recipient',  # Отключение получателей
        ])

        # 3. Права для работы с сообщениями (Message)
        permissions_to_add.extend([
            'can_view_all_messages',  # Просмотр всех сообщений
        ])

        # 4. Права для работы с рассылками (Mailing)
        permissions_to_add.extend([
            'can_view_all_mailing',  # Просмотр всех рассылок
            'can_disable_mailing',  # Отключение рассылок
        ])

        # 5. Права для работы с логами (MailingLog)
        permissions_to_add.extend([
            'can_view_all_logs',  # Просмотр всех логов
        ])

        # Находим и добавляем все права
        for codename in permissions_to_add:
            try:
                perm = Permission.objects.get(codename=codename)
                group.permissions.add(perm)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'Право "{codename}" не найдено в базе. Пропускаем.'
                ))

        self.stdout.write(self.style.SUCCESS(
            'Группе "Менеджер" назначены следующие права:\n'
            '1. Пользователи:\n'
            '   - Просмотр списка пользователей\n'
            '   - Блокировка пользователей (изменение is_active)\n\n'
            '2. Получатели:\n'
            '   - Просмотр всех клиентов\n'
            '   - Отключение получателей\n\n'
            '3. Сообщения:\n'
            '   - Просмотр всех сообщений\n\n'
            '4. Рассылки:\n'
            '   - Просмотр всех рассылок\n'
            '   - Отключение рассылок\n\n'
            '5. Логи:\n'
            '   - Просмотр всех логов рассылок'
        ))