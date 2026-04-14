from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from speakproject.models import Booking
from django.core.mail import send_mail

class Command(BaseCommand):
    help = "Send session reminders"

    def handle(self, *args, **kwargs):
        now = timezone.localtime(timezone.now())
        target_time = now + timedelta(minutes=10)

        bookings = Booking.objects.filter(
            paid=True,
            status='paid',
            reminder_sent=False,
            slot__start_time__range=(now, target_time)
        )

        for booking in bookings:
            send_mail(
                subject="⏰ Your session starts soon!",
                message=f"""
Hi {booking.user.username},

Your session with {booking.counselor.username} starts in 10 minutes.

Please join on time 💜

- Speak Team
                """,
                from_email=None,
                recipient_list=[booking.user.email],
            )

            booking.reminder_sent = True
            booking.save()

            self.stdout.write(f"✅ Reminder sent to {booking.user.email}")