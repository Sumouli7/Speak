from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from .models import Booking
import pytz
import os


# ---------------- EMAIL FOOTER ---------------- #

EMAIL_FOOTER_HTML = """
<hr>

<table width="100%" style="font-size:12px; color:#555;">
<tr>
<td>
<strong>Speak</strong><br>
A safe, global mental wellness platform
</td>
</tr>

<tr>
<td>
<table width="100%">
<tr>
<td>
<strong>Support</strong><br>
support@speak.org
</td>

<td align="right">
<strong>Grievances</strong><br>
admin@speak.org
</td>
</tr>
</table>
</td>
</tr>

<tr>
<td style="padding-top:10px;">
© 2026 Speak. Designed with care.
</td>
</tr>
</table>
"""


# ---------------- TIMEZONE ---------------- #

def convert_to_user_timezone(dt, user):
    country = user.profile.country

    if country == "IN":
        tz = pytz.timezone("Asia/Kolkata")
    elif country == "NG":
        tz = pytz.timezone("Africa/Lagos")
    else:
        tz = pytz.UTC

    return dt.astimezone(tz)
def get_currency_symbol(user):
    if user.profile.country == "IN":
        return "₹"
    elif user.profile.country == "NG":
        return "₦"
    else:
        return "₹"


# ---------------- PDF ---------------- #

def generate_invoice_pdf(booking):
    file_path = os.path.join(settings.MEDIA_ROOT, f"invoice_{booking.id}.pdf")

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    logo_path = os.path.join(settings.BASE_DIR, "static/images/logo.png")

    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=2*inch, height=1*inch))
        elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>SPEAK</b>", styles['Title']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>Session Invoice</b>", styles['Heading2']))
    elements.append(Spacer(1, 20))

    local_time = convert_to_user_timezone(booking.slot.start_time, booking.user)

    elements.append(Paragraph("<b>Session Details</b>", styles['Heading3']))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"User: {booking.user.username}", styles['Normal']))
    elements.append(Paragraph(f"Counselor: {booking.counselor.username}", styles['Normal']))
    elements.append(Paragraph(f"Date: {local_time.strftime('%Y-%m-%d')}", styles['Normal']))
    elements.append(Paragraph(f"Time: {local_time.strftime('%I:%M %p')}", styles['Normal']))
    currency = get_currency_symbol(booking.user)
    elements.append(Paragraph(f"Amount Paid: {currency}{booking.amount}", styles['Normal']))

    elements.append(Spacer(1, 20))

    if hasattr(booking, "notes") and booking.notes:
        elements.append(Paragraph("<b>Session Summary</b>", styles['Heading2']))
        elements.append(Spacer(1, 10))

        for line in booking.notes.split("\n"):
            elements.append(Paragraph(line, styles['Normal']))
            elements.append(Spacer(1, 5))

    elements.append(Spacer(1, 20))

    if booking.rating:
        elements.append(Paragraph("<b>Rating</b>", styles['Heading3']))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"{booking.rating} / 5 ⭐", styles['Normal']))

    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Thank you for choosing Speak 💜", styles['Italic']))

    doc.build(elements)

    return file_path


# ---------------- INVOICE EMAIL ---------------- #

def send_invoice_email(user_email, booking):
    local_time = convert_to_user_timezone(booking.slot.start_time, booking.user)
    currency = get_currency_symbol(booking.user)

    subject = "Payment Successful - Invoice Attached"
    body = f"""
Hi {booking.user.username},

Your session has been successfully booked.

Counselor: {booking.counselor.username}
Time: {local_time.strftime('%I:%M %p')}
Amount: {currency}{booking.amount}

Please find your invoice attached.

Thanks,
Speak Team
"""

    pdf_path = generate_invoice_pdf(booking)

    email = EmailMessage(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
    )

    email.attach_file(pdf_path)
    email.send(fail_silently=False)

# ---------------- REMINDER EMAIL ---------------- #

def send_session_reminders():
    now = timezone.now()
    upcoming = now + timedelta(minutes=10)

    sessions = Booking.objects.filter(status='paid')

    for booking in sessions:
        session_time = booking.slot.start_time

        if now <= session_time <= upcoming:
            local_time = convert_to_user_timezone(session_time, booking.user)

            email = EmailMessage(
                subject="⏰ Session Reminder",
                body=f"""
                <p>Hi {booking.user.username},</p>

                <p>Your session with <b>{booking.counselor.username}</b> starts in 10 minutes.</p>

                <p><b>Time:</b> {local_time.strftime('%I:%M %p')}</p>

                <p>Please be ready!</p>

                <p>- Speak Team</p>

                {EMAIL_FOOTER_HTML}
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[booking.user.email],
            )

            email.content_subtype = "html"
            email.send()


# ---------------- PAYMENT EMAIL ---------------- #

from django.core.mail import EmailMultiAlternatives
def send_payment_confirmation_email(booking):
    print("🔥 PAYMENT EMAIL FUNCTION CALLED")

    from django.core.mail import send_mail
    from django.conf import settings

    send_mail(
        "TEST EMAIL",
        "If you see this, SMTP works",
        settings.EMAIL_HOST_USER,
        ["sumouli05ece@gmail.com"],  # 🔥 PUT YOUR REAL EMAIL HERE
        fail_silently=False,
    )
