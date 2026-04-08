from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from speakproject.models import EmployeeProfile, EmployeeSlot


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        start = timezone.now().replace(second=0, microsecond=0)
        for employee in EmployeeProfile.objects.filter(is_approved=True):
            for i in range(48):
                s = start + timedelta(minutes=i * 10)
                e = s + timedelta(minutes=10)
                EmployeeSlot.objects.get_or_create(
                    employee=employee,
                    start_time=s,
                    end_time=e,
                )