from django.core.management.base import BaseCommand
from django.utils import timezone
from mailing_service.models import Mailing

class Command(BaseCommand):
    help = 'Send scheduled mailings'

    def handle(self, *args, **options):
        now = timezone.now()
        mailings = Mailing.objects.filter(
            is_active=True,
            first_shipment__lte=now,
            end_shipment__gte=now
        )

        for mailing in mailings:
            self.stdout.write(f"Sending mailing #{mailing.id}")
            mailing.send()