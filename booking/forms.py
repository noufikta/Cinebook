from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Seat


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "email",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "An account with this email already exists."
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        user.first_name = self.cleaned_data["first_name"].strip()

        if commit:
            user.save()

        return user


class BookingForm(forms.Form):
    seats = forms.MultipleChoiceField(
        choices=(),
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, show=None, **kwargs):
        super().__init__(*args, **kwargs)

        if show:
            available = Seat.objects.filter(
                show=show,
                status=Seat.Status.AVAILABLE,
            ).order_by("seat_number")

            self.fields["seats"].choices = [
                (seat.seat_number, seat.seat_number)
                for seat in available
            ]

    def clean_seats(self):
        labels = self.cleaned_data["seats"]

        if len(labels) > 10:
            raise ValidationError(
                "Maximum 10 seats per booking."
            )

        if len(labels) != len(set(labels)):
            raise ValidationError(
                "Duplicate seats are not allowed."
            )

        return labels