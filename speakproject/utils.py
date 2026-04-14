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
# utils.py

from django.conf import settings
from sib_api_v3_sdk import Configuration, ApiClient
from sib_api_v3_sdk.api import transactional_emails_api
from sib_api_v3_sdk.models import SendSmtpEmail
from django.conf import settings
from sib_api_v3_sdk import Configuration, ApiClient
from sib_api_v3_sdk.api import transactional_emails_api
from sib_api_v3_sdk.models import SendSmtpEmail


def send_payment_confirmation_email(booking):
    print("API KEY:", settings.BREVO_API_KEY)


    configuration = Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY

    api_instance = transactional_emails_api.TransactionalEmailsApi(
        ApiClient(configuration)
    )

    send_smtp_email = SendSmtpEmail(
        to=[{"email": booking.user.email}],
        sender={"email": "dospeakwithus@getspeakhub.org", "name": "SpeakHub"},
        subject="Payment Successful 🎉",
        html_content=f"""
<div style="font-family: Arial, sans-serif; line-height:1.6; color:#333;">

    <h2 style="color:#6C63FF;">Payment Successful & Booking Confirmed 🎉</h2>

    <p>Hello <b>{booking.user.username}</b>,</p>

    <p>Your session has been successfully booked. Here are your details:</p>

    <hr>

    <p><b>👤 Name:</b> {booking.user.username}</p>
    <p><b>🧑‍⚕️ Counsellor:</b> {booking.counselor.username}</p>
    <p><b>📅 Scheduled Session:</b>{booking.slot.start_time.strftime("%d %B %Y, %I:%M %p")}</p>
    <p><b>⏳ Duration:</b> {booking.slot.duration} minutes</p>
    <p><b>💰 Consultation Fees:</b>{get_currency_symbol(booking.user)}{booking.amount}</p>
    <p><b>✅ Status:</b> Paid & Booked</p>

    <hr>

    <p>Thank you for choosing <b>Speak</b> 💜</p>

    <br>

    <div style="font-size:14px; color:#555;">
        <p><b>Speak</b></p>
        <p>A safe, global mental wellness platform connecting<br>
        people across India, Ethiopia, and Nigeria.</p>

        <p><b>Contact</b><br>
        dospeakwithus@getspeakhub.org</p>

        <p style="font-size:12px; color:#999;">
        © 2026 Speak. Designed with care.
        </p>
    </div>

</div>
"""
    )

    try:
        response = api_instance.send_transac_email(send_smtp_email)
        print("✅ Email sent:", response)
    except Exception as e:
        print("❌ Email error:", str(e))


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
from sib_api_v3_sdk import Configuration, ApiClient
from sib_api_v3_sdk.api import transactional_emails_api
from sib_api_v3_sdk.models import SendSmtpEmail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Booking


def send_session_reminders():
    print("🔔 Running reminder scheduler...")

    configuration = Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY

    api_instance = transactional_emails_api.TransactionalEmailsApi(
        ApiClient(configuration)
    )

    now = timezone.now()
    window_start = now + timedelta(minutes=28)
    window_end = now + timedelta(minutes=32)

    bookings = Booking.objects.filter(
        status='paid',
        reminder_sent=False,
        slot__start_time__gte=window_start,
        slot__start_time__lte=window_end,
    ).select_related('user', 'counselor', 'slot')

    for booking in bookings:
        try:
            formatted_time = booking.slot.start_time.strftime("%d %B %Y, %I:%M %p")

            html_content = f"""
            <div style="font-family: Arial; color:#333;">
                <h2 style="color:#FF6B6B;">⏰ Session Reminder</h2>

                <p>Hello <b>{booking.user.username}</b>,</p>

                <p>Your session is starting in <b>30 minutes</b>.</p>

                <hr>

                <p><b>👩‍⚕️ Counsellor:</b> {booking.counselor.username}</p>
                <p><b>📅 Time:</b> {formatted_time}</p>
                <p><b>🔗 Join Link:</b> {booking.meeting_link}</p>

                <hr>

                <p>Be ready and take care 💜</p>

                <br>

                <div style="font-size:13px; color:#666;">
                    <p><b>Speak</b></p>
                    <p>A safe, global mental wellness platform</p>
                    <p>dospeakwithus@getspeakhub.org</p>
                </div>
            </div>
            """

            email = SendSmtpEmail(
                to=[{"email": booking.user.email}],
                sender={"email": "dospeakwithus@getspeakhub.org", "name": "Speak"},
                subject="⏰ Your session starts in 30 minutes",
                html_content=html_content
            )

            api_instance.send_transac_email(email)

            booking.reminder_sent = True
            booking.save(update_fields=['reminder_sent'])

            print(f"✅ Reminder sent: {booking.id}")

        except Exception as e:
            print(f"❌ Reminder failed: {str(e)}")