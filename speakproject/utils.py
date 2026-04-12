from django.core.mail import EmailMessage, send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from .models import Booking
import pytz
import os


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


# ---------------- PAYMENT CONFIRMATION EMAIL ---------------- #
def send_payment_confirmation_email(booking):
    import traceback
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    print("🔥 EMAIL FUNCTION CALLED")
    print("TO:", booking.user.email)

    try:
        local_time = convert_to_user_timezone(booking.slot.start_time, booking.user)
        currency = get_currency_symbol(booking.user)
        counselor_name = booking.counselor.get_full_name() or booking.counselor.username

        message = Mail(
            from_email='speakappplatform@gmail.com',
            to_emails=booking.user.email,
            subject='Your Session is Confirmed 💬',
            plain_text_content=f"""Hi {booking.user.username},

Your session has been successfully booked! 🎉

Counselor   : {counselor_name}
Date        : {local_time.strftime('%d %B %Y')}
Time        : {local_time.strftime('%I:%M %p')}
Duration    : {booking.duration} minutes
Amount Paid : {currency}{booking.amount}

– Team Speak
"""
        )

        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(f"✅ EMAIL SENT — status: {response.status_code}")

    except Exception as e:
        print("❌ EMAIL ERROR:", str(e))
        traceback.print_exc()


# ---------------- PDF GENERATOR ---------------- #

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

    elements.append(Paragraph(f"User: {booking.user.username}", styles['Normal']))
    elements.append(Paragraph(f"Counselor: {booking.counselor.username}", styles['Normal']))
    elements.append(Paragraph(f"Time: {local_time}", styles['Normal']))

    currency = get_currency_symbol(booking.user)
    elements.append(Paragraph(f"Amount Paid: {currency}{booking.amount}", styles['Normal']))

    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Thank you for choosing Speak 💜", styles['Italic']))

    doc.build(elements)

    return file_path


# ---------------- INVOICE EMAIL ---------------- #

def send_invoice_email(user_email, booking):
    try:
        pdf_path = generate_invoice_pdf(booking)

        email = EmailMessage(
            subject="Payment Successful - Invoice",
            body=f"""
Hi {booking.user.username},

Your session has been booked successfully.

Please find your invoice attached.

Thanks,
Speak Team
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )

        email.attach_file(pdf_path)
        email.send(fail_silently=False)

        print(f"✅ Invoice email sent to {user_email}")

    except Exception as e:
        print(f"❌ Invoice email failed: {str(e)}")


# ---------------- REMINDER EMAIL ---------------- #

def send_session_reminders():
    now = timezone.now()
    window_start = now + timedelta(minutes=28)
    window_end = now + timedelta(minutes=32)

    bookings = Booking.objects.filter(
        status='paid',
        reminder_sent=False,
        slot__start_time__gte=window_start,
        slot__start_time__lte=window_end,
    )

    for booking in bookings:
        try:
            local_time = convert_to_user_timezone(booking.slot.start_time, booking.user)

            email = EmailMessage(
                subject="⏰ Session Reminder - Speak",
                body=f"""
Hi {booking.user.username},

Your session starts in 30 minutes.

Time: {local_time}

Join link: {booking.meeting_link}

- Speak Team
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[booking.user.email],
            )

            email.send(fail_silently=False)

            booking.reminder_sent = True
            booking.save(update_fields=['reminder_sent'])

            print(f"✅ Reminder sent for booking {booking.id}")

        except Exception as e:
            print(f"❌ Reminder failed: {str(e)}")