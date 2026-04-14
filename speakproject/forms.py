from django import forms
from django.contrib.auth.models import User
from .models import Profile


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    user_type = forms.ChoiceField(choices=Profile.USER_TYPE)
    gender = forms.ChoiceField(choices=Profile.GENDER_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

            # ✅ Create Profile with gender
            Profile.objects.create(
                user=user,
                user_type=self.cleaned_data['user_type'],
                gender=self.cleaned_data['gender']
            )

        return user