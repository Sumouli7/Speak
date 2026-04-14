from django.core.mail import send_mail
from django.conf import settings


def send_booking_email(user, booking):
    subject = "🎉 Session Booked Successfully"

    message = f"""
Hi {user.username},

Your session has been successfully booked!

🧑‍⚕️ Counselor: {booking.slot.counselor.username}
📅 Date & Time: {booking.slot.start_time}

Please join on time.

Thank you for using Speak 💙
"""

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )