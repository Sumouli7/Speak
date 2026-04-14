from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal


# 🌍 CURRENCY MAP
CURRENCY_MAP = {
    'IN': 'INR',
    'NG': 'NGN',
}


# ---------------- PROFILE ---------------- #
class Profile(models.Model):
    USER_TYPE = (
        ('patient', 'Patient'),
        ('counselor', 'Counselor'),
    )

    COUNTRY = (
        ('IN', 'India'),
        ('NG', 'Nigeria'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE)
    country = models.CharField(max_length=5, choices=COUNTRY, default='IN')

    is_approved = models.BooleanField(default=False)

    razorpay_account_id = models.CharField(max_length=100, blank=True, null=True)

    payout_upi = models.CharField(max_length=100, blank=True, null=True)
    account_holder_name = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)

    bank_code = models.CharField(max_length=50, blank=True, null=True)
    currency = models.CharField(max_length=10, default="INR")

    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    govt_id = models.FileField(upload_to='govt_ids/', null=True, blank=True)
    certificate = models.FileField(upload_to='certificates/', null=True, blank=True)

    description = models.TextField(blank=True, null=True)
    avg_rating = models.FloatField(default=4.5)

    def __str__(self):
        return f"{self.user.username} ({self.user_type})"


# ---------------- SLOT ---------------- #
class Slot(models.Model):
    counselor = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    duration = models.IntegerField(default=30)  # in minutes

    def clean(self):
        if self.start_time <= timezone.now() + timedelta(hours=4):
            raise ValidationError("Slot must be at least 4 hours in advance")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def end_time(self):
        return self.start_time + timedelta(minutes=self.duration)

    def __str__(self):
        return f"{self.counselor.username} - {self.start_time.strftime('%Y-%m-%d %I:%M %p')}"


# ---------------- BOOKING ---------------- #
class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # 🔗 RELATIONS
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_bookings')
    counselor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='counselor_bookings')
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)

    # ⏱ SESSION
    duration = models.IntegerField(default=30)
    meeting_link = models.URLField(blank=True, null=True)

    # 💰 PAYMENT (handled in views.py)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid = models.BooleanField(default=False)
    currency = models.CharField(max_length=10, default='INR')

    original_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # 💸 EARNINGS (handled in views.py)
    counselor_earning = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_earning = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # 🏦 PAYOUT
    payout_done = models.BooleanField(default=False)
    payout_date = models.DateTimeField(null=True, blank=True)

    # 📊 STATUS
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reminder_sent = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)

    # ⭐ REVIEW
    rating = models.IntegerField(null=True, blank=True)
    review = models.TextField(null=True, blank=True)

    # 🕒 CREATED
    created_at = models.DateTimeField(auto_now_add=True)

    # 💎 DISPLAY AMOUNT (FIXED — NO CONVERSION)
    @property
    def display_amount(self):
        if self.currency == "NGN":
            return f"₦{self.amount}"
        return f"₹{self.amount}"

    # 🎯 SESSION STATES
    @property
    def is_completed(self):
        return timezone.now() > (self.slot.start_time + timedelta(minutes=self.duration))

    @property
    def is_ongoing(self):
        now = timezone.now()
        start = self.slot.start_time
        end = start + timedelta(minutes=self.duration)
        return start <= now <= end

    @property
    def is_upcoming(self):
        return timezone.now() < self.slot.start_time

    def can_join(self):
        now = timezone.now()
        start = self.slot.start_time
        end = start + timedelta(minutes=self.duration)
        return (start - timedelta(minutes=10)) <= now <= end

    # 🔗 Auto meeting link (safe)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.meeting_link:
            self.meeting_link = f"https://meet.jit.si/session_{self.id}"
            super().save(update_fields=['meeting_link'])

    def __str__(self):
        return f"{self.user.username} → {self.counselor.username} ({self.status})"