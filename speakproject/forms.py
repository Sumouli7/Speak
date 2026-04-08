from django import forms
from django.contrib.auth.models import User
from .models import Profile

class RegisterForm(forms.ModelForm):
    # Use the choices defined in your Profile model for consistency
    user_type = forms.ChoiceField(choices=Profile.USER_TYPES)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        # 1. Create the user object but don't save to DB yet
        user = super().save(commit=False)
        
        # 2. Hash the password (crucial for login to work!)
        user.set_password(self.cleaned_data["password"])
        
        if commit:
            user.save()
        return user