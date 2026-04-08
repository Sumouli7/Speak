from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from .models import Profile, Booking


# 🔥 FORM VALIDATION (MOVED FROM MODEL)
class ProfileAdminForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()

        user_type = cleaned_data.get('user_type')
        country = cleaned_data.get('country')
        payout_upi = cleaned_data.get('payout_upi')
        ifsc_code = cleaned_data.get('ifsc_code')
        bank_code = cleaned_data.get('bank_code')

        if user_type == 'counselor':
            if country == 'IN':
                if not payout_upi:
                    raise ValidationError("UPI is required for Indian counselors")
                if not ifsc_code:
                    raise ValidationError("IFSC code is required for Indian counselors")

            elif country == 'NG':
                if not bank_code:
                    raise ValidationError("Bank code is required for Nigerian counselors")

        return cleaned_data


# 🔥 PROFILE ADMIN
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    form = ProfileAdminForm   # ✅ attach form

    list_display = ('user', 'user_type', 'is_approved')
    list_filter = ('user_type', 'is_approved')
    list_editable = ('is_approved',)


# 🔥 BOOKING ADMIN
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'counselor', 'amount', 'status', 'payout_done')
    list_filter = ('status', 'payout_done')