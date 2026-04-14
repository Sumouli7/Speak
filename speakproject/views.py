from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings

from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

import razorpay
import os
from .models import Booking, Profile, Slot
from django.db.models import Sum
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from io import BytesIO
from django.core.mail import EmailMessage
from .utils import send_payment_confirmation_email
import threading
# ---------------- HOME ---------------- #
def main_home(request):
    return render(request, "speakproject/main_home.html", {
        "hide_nav": True
    })


from django.http import HttpResponse

from django.contrib.auth import authenticate, login

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile   # ✅ IMPORTANT

# ---------------- USER LOGIN ---------------- #
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('user_dashboard')  
        else:
            return render(request, 'speakproject/user_login.html', {
                'error': 'Invalid username or password'
            })

    return render(request, 'speakproject/user_login.html')


# ---------------- USER REGISTER ---------------- #
def user_register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            return render(request, 'speakproject/user_register.html', {
                'error': 'Username already exists'
            })

        # ✅ Create user
        email = request.POST.get("email")

        user = User.objects.create_user(
             username=username,
             email=email,
             password=password
        )
        user.save()

        # ✅ VERY IMPORTANT: Create profile as patient
        Profile.objects.create(
            user=user,
            user_type='patient'
        )

        return redirect('login')

    return render(request, 'speakproject/user_register.html')

#------------------Employee Login------------------#
def employee_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user:
            from .models import Profile
            profile, created = Profile.objects.get_or_create(user=user)

            # 🔒 Only counselor allowed
            if profile.user_type != 'counselor':
                messages.error(request, "Not a counselor account ❌")
                return redirect("employee_login")

            # 🔥 MAIN APPROVAL CHECK
            if not profile.is_approved:
                messages.error(request, "Your account is pending admin approval ⏳")
                return redirect("employee_login")

            login(request, user)
            return redirect('counselor_dashboard')

        else:
            messages.error(request, "Invalid credentials ❌")

    return render(request, "speakproject/employee_login.html")


# Employee register#
def employee_register(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST.get("email")
        country = request.POST['country']
        gender = request.POST.get('gender')

        if not gender:
            messages.error(request, "Gender is required ❌")
            return redirect("employee_register")

        print("GENDER:", gender)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists ❌")
            return redirect("employee_register")

        # ✅ Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # ✅ Create profile
        profile = Profile.objects.create(
            user=user,
            user_type='counselor',
            country=country,
            gender=gender,
            account_holder_name=request.POST.get('account_holder_name'),
            bank_name=request.POST.get('bank_name'),
            account_number=request.POST.get('account_number'),
            ifsc_code=request.POST.get('ifsc_code'),
        )

        # ✅ Currency
        if country == "NG":
            profile.currency = "NGN"
        elif country == "IN":
            profile.currency = "INR"
        else:
            messages.error(request, "Unsupported country ❌")
            user.delete()
            return redirect("employee_register")

        # ✅ Extra fields
        profile.description = request.POST.get('description')
        profile.profile_picture = request.FILES.get('profile_picture')

        profile.save()

        messages.success(request, "Counselor registered successfully 🎉")
        return redirect("employee_login")

    return render(request, "speakproject/employee_register.html")
@login_required
def create_slot(request):
    if request.user.profile.user_type != 'counselor':
        return redirect('main_home')

    if request.method == "POST":
        try:
            start_time = request.POST.get("start_time")
            duration = request.POST.get("duration")

            # Convert to datetime
            start_time = datetime.fromisoformat(start_time)

            # Make timezone aware
            if timezone.is_naive(start_time):
                start_time = timezone.make_aware(start_time)

            # Create slot
            Slot.objects.create(
                counselor=request.user,
                start_time=start_time,
                duration=int(duration)
            )

            messages.success(request, "Slot created successfully 🎉")
            return redirect("counselor_dashboard")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return render(request, "speakproject/create_slot.html")
# Submit Rating #

from django.views.decorators.http import require_POST
@require_POST
@login_required
def submit_rating(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # 🔒 Only booking owner
    if request.user != booking.user:
        return redirect("user_dashboard")

    # 🔒 Only after session ends
    if booking.slot.end_time > timezone.now():
        messages.error(request, "You can rate only after session ends ⏳")
        return redirect("user_dashboard")

    # 🔒 Prevent duplicate rating
    if booking.rating:
        messages.warning(request, "You already rated this session ⭐")
        return redirect("user_dashboard")

    rating = request.POST.get("rating")
    review = request.POST.get("review")

    if rating:
        booking.rating = int(rating)
        booking.review = review
        booking.save()

        # 🔥 UPDATE COUNSELOR AVG RATING
        ratings = Booking.objects.filter(
            counselor=booking.counselor,
            rating__isnull=False
        ).values_list('rating', flat=True)

        avg = sum(ratings) / len(ratings)

        profile = Profile.objects.get(user=booking.counselor)
        profile.avg_rating = round(avg, 1)
        profile.save()

        messages.success(request, "⭐ Thanks for your feedback!")

    return redirect("user_dashboard")
# ---------------- LOGOUT ---------------- #
def user_logout(request):
    logout(request)
    return redirect("main_home")


# ---------------- USER DASHBOARD ---------------- #
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import Profile, Booking, Slot
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import random

@login_required
def user_home(request):
    # ✅ Ensure profile exists with correct default
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'user_type': 'patient'}
    )

    # ✅ Prevent wrong user types (no redirect loop)
    if profile.user_type != 'patient':
        return HttpResponse("Access denied: Not a patient user")

    now = timezone.now()

    booked_slot_ids = Booking.objects.values_list('slot_id', flat=True)

    slots = Slot.objects.filter(
        start_time__gte=timezone.now(),
    ).exclude(
        id__in=booked_slot_ids
    ).select_related('counselor', 'counselor__profile').order_by('start_time')

    # ✅ Get user bookings
    bookings = Booking.objects.filter(
        user=request.user
    ).select_related('slot', 'counselor')

    # ✅ Join session logic
    for b in bookings:
        start = b.slot.start_time
        end = start + timedelta(minutes=b.duration)
        b.can_join = (start - timedelta(minutes=10)) <= now <= end

    # 📊 Stats
    total_bookings = bookings.count()
    completed_sessions = bookings.filter(status='completed').count()

    # 🧠 Tips
    all_tips = [
        "Take 5 deep breaths when stressed 🌬",
        "Drink enough water 💧",
        "Talk to someone you trust ❤️",
        "Sleep at least 7–8 hours 😴",
        "Take breaks during work/study ⏳",
        "Go for a short walk 🚶‍♀️",
    ]
    tips = random.sample(all_tips, 3)

    return render(request, "speakproject/dashboard.html", {
        "slots": slots,
        "bookings": bookings,
        "now": now,
        "total_bookings": total_bookings,
        "completed_sessions": completed_sessions,
        "tips": tips,
    })
# ---------------- COUNSELOR DASHBOARD ---------------- #
@login_required
def counselor_home(request):
    if request.user.profile.user_type != 'counselor':
        return redirect('counselor_dashboard')

    now = timezone.now()

    profile = Profile.objects.filter(user=request.user).first()
    CURRENCY_SYMBOLS = {
    "INR": "₹",
    "NGN": "₦",
}

# ✅ Get currency from profile (STRICT)
    currency = profile.currency

    if not currency:
     raise ValueError("Currency not set for this user")

    symbol = CURRENCY_SYMBOLS[currency]

    bookings = Booking.objects.filter(
        counselor=request.user,
        paid=True
    ).select_related('user', 'slot')

    total_earnings = bookings.aggregate(
        total=Sum('counselor_earning')
    )['total'] or 0

    ongoing = []
    upcoming = []
    completed = []

    for b in bookings:
        if b.is_ongoing:
            ongoing.append(b)
        elif b.is_upcoming:
            upcoming.append(b)
        else:
            completed.append(b)

        session_end = b.slot.start_time + timedelta(minutes=b.duration)

        if timezone.now() > session_end and b.status != 'completed':
         b.status = 'completed'
         b.save(update_fields=['status'])

         

    return render(request, "speakproject/employee_dashboard.html", {
        "ongoing": ongoing,
        "upcoming": upcoming,
        "completed": completed,
        "profile": profile,
        "now": now,
        "total_earnings": total_earnings,
        "symbol": symbol,
    })


# ---------------- BOOK SESSION ---------------- #
from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

@login_required
def book_session(request, slot_id):

    slot = get_object_or_404(Slot, id=slot_id)

    # ❌ Prevent double booking
    if Booking.objects.filter(slot=slot).exists():
        messages.error(request, "Slot already booked ❌")
        return redirect("user_dashboard")

    # 🔥 Get counselor currency
    profile = Profile.objects.get(user=slot.counselor)
    currency = profile.currency

    # 🔥 Set pricing FIRST
    if currency == "INR":
        base_price = Decimal("20")
        per_10_min = Decimal("30")

    elif currency == "NGN":
        base_price = Decimal("0")
        per_10_min = Decimal("1000")

    else:
        base_price = Decimal("0")
        per_10_min = Decimal("50")

    # 🔥 Calculate total
    duration = slot.duration
    duration_decimal = Decimal(duration)

    total = base_price + (per_10_min * (duration_decimal / Decimal("10")))

    # ✅ Create booking
    booking = Booking.objects.create(
        user=request.user,
        counselor=slot.counselor,
        slot=slot,
        duration=duration,
        amount=total,
        original_amount=total,
        currency=currency
    )

    return redirect("payment", booking_id=booking.id)

# ---------------- PAYMENT (ADVANCE ₹20) ---------------- #
@login_required
def payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.amount <= 0:
     messages.error(request, "Invalid amount. Please book again.")
     return redirect("user_dashboard")
    
    print("BOOKING AMOUNT:", booking.amount)

    # 🚫 Prevent double payment
    if booking.paid:
        return redirect("user_dashboard")

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    order = client.order.create({
        "amount": int(booking.amount * 100),  # ✅ FULL AMOUNT
        "currency": booking.currency,
        "payment_capture": "1"
    })
    booking.razorpay_order_id = order["id"]
    booking.save()

    return render(request, "speakproject/payment.html", {
        "order_id": order["id"],
        "booking": booking,
        "amount": order["amount"],
        "razorpay_key": settings.RAZORPAY_KEY_ID
    })



# ---------------- PAYMENT SUCCESS ---------------- #
def payment_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    booking.paid = True
    booking.status = "paid"
    booking.save()

    try:
        send_payment_confirmation_email(booking)
    except Exception as e:
        print(f"❌ Email failed: {str(e)}")

    return render(request, "speakproject/payment_success.html", {
        "booking": booking
    })



# ---------------- SESSION ROOM ---------------- #
@login_required
def session_room(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # 🔥 BLOCK IF PAYMENT NOT DONE
    if not booking.paid:
        return redirect("payment", booking_id=booking.id)
    room_name = f"SpeakSession{booking.id}"

    is_counselor = False
    if request.user == booking.counselor:
        is_counselor = True

    return render(request, "speakproject/session.html", {
        "booking": booking,
        "room_name": room_name,
        "is_counselor": is_counselor,
    })




# ---------------- PDF GENERATOR ---------------- #
def generate_session_pdf(booking):
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []

    # 🧠 TITLE
    content.append(Paragraph("🧠 Speak - Session Summary", styles['Title']))
    content.append(Spacer(1, 12))

    # 👤 USER + COUNSELOR
    content.append(Paragraph(f"<b>User:</b> {booking.user.username}", styles['Normal']))
    content.append(Paragraph(f"<b>Counselor:</b> {booking.counselor.username}", styles['Normal']))
    content.append(Spacer(1, 12))

    # ⭐ RATING
    content.append(Paragraph("<b>Rating:</b>", styles['Heading2']))
    content.append(Paragraph(str(booking.rating or "Not given"), styles['Normal']))
    content.append(Spacer(1, 10))

    # 🧠 FEEDBACK
    content.append(Paragraph("<b>Feedback:</b>", styles['Heading2']))
    content.append(Paragraph(booking.review or "No feedback provided", styles['Normal']))
    content.append(Spacer(1, 10))

    # 🌿 SUGGESTIONS
    content.append(Paragraph("<b>Suggestions:</b>", styles['Heading2']))
    content.append(Paragraph(
        getattr(booking, "suggestions", "No suggestions provided"),
        styles['Normal']
    ))
    content.append(Spacer(1, 10))

    # ✍️ CLARIFICATION
    content.append(Paragraph("<b>Clarification:</b>", styles['Heading2']))
    content.append(Paragraph(
        getattr(booking, "clarification", "No clarification provided"),
        styles['Normal']
    ))

    doc.build(content)
    buffer.seek(0)

    return buffer


# ---------------- EMAIL SENDER ---------------- #
def send_session_email(booking):
    try:
        pdf_buffer = generate_session_pdf(booking)

        email = EmailMessage(
            subject="🧠 Your Session Summary - Speak",
            body=(
                f"Hi {booking.user.username},\n\n"
                "Thank you for your session 💜\n\n"
                "Your session summary is attached as a PDF.\n\n"
                "Stay strong 🌿\n"
                "- Speak Team"
            ),
            to=[booking.user.email],
        )

        email.attach(
            "session_summary.pdf",
            pdf_buffer.read(),
            "application/pdf"
        )

        email.send()

        print(f"✅ Email sent to {booking.user.email}")

    except Exception as e:
        print(f"❌ Email failed: {str(e)}")