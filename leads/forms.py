from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import BusinessProfile, Lead


class PublicLeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{classes} form-control'.strip()


class LeadUpdateForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['status', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class SignupForm(UserCreationForm):
    business_name = forms.CharField(max_length=255)
    notification_email = forms.EmailField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'email',
            'business_name',
            'notification_email',
            'password1',
            'password2',
        )

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, _ = BusinessProfile.objects.get_or_create(
                user=user,
                defaults={
                    'business_name': self.cleaned_data['business_name'],
                    'notification_email': self.cleaned_data['notification_email']
                    or user.email,
                },
            )
            profile.business_name = self.cleaned_data['business_name']
            profile.notification_email = (
                self.cleaned_data['notification_email'] or user.email
            )
            profile.save()
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class ProfileForm(forms.ModelForm):
    class Meta:
        model = BusinessProfile
        fields = ['business_name', 'notification_email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {
                'class': 'form-control form-control-lg',
                'placeholder': 'contoh@bisnis.com',
                'autofocus': 'autofocus',
            }
        )
        self.fields['password'].widget.attrs.update(
            {
                'class': 'form-control form-control-lg',
                'placeholder': '••••••••',
                'autocomplete': 'current-password',
            }
        )
