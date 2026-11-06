import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator


class Movie(models.Model):
    title = models.CharField(max_length=160)
    description = models.TextField()
    genre = models.CharField(max_length=80)
    language = models.CharField(max_length=50, default="Malayalam")
    duration_minutes = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(600)]
    )
    certificate = models.CharField(max_length=10, default="UA")
    poster_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Show(models.Model):
    movie = models.ForeignKey(
        Movie, on_delete=models.PROTECT, related_name="shows"
    )
    cinema_name = models.CharField(max_length=120)
    screen_name = models.CharField(max_length=60, default="Screen 1")
    starts_at = models.DateTimeField()
    seat_capacity = models.PositiveSmallIntegerField(
        default=40,
        validators=[MinValueValidator(1), MaxValueValidator(300)],
    )
    ticket_price = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.movie} - {self.cinema_name} - {self.starts_at}"


class Seat(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        BOOKED = "BOOKED", "Booked"

    show = models.ForeignKey(
        Show, on_delete=models.CASCADE, related_name="seats"
    )
    seat_number = models.CharField(max_length=8)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )

    class Meta:
        ordering = ["seat_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["show", "seat_number"],
                name="unique_seat_per_show",
            )
        ]

    def __str__(self):
        return f"{self.show_id}: {self.seat_number}"


class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    class PaymentStatus(models.TextChoices):
        PAID = "PAID", "Paid (simulated)"
        REFUNDED = "REFUNDED", "Refunded (simulated)"

    booking_reference = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="movie_bookings",
    )
    show = models.ForeignKey(
        Show, on_delete=models.PROTECT, related_name="bookings"
    )
    seats = models.ManyToManyField(Seat, related_name="bookings")
    seat_count = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.CONFIRMED
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PAID,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(seat_count__gte=1),
                name="booking_seat_count_positive",
            ),
            models.CheckConstraint(
                condition=Q(total_amount__gte=0),
                name="booking_amount_nonnegative",
            ),
        ]

    def __str__(self):
        return str(self.booking_reference)