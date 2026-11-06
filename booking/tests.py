from django.test import TestCase

# Create your tests here.
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import Movie, Show, Seat, Booking


class BookingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student",
            password="StrongPass123!",
            email="student@example.com",
        )

        self.movie = Movie.objects.create(
            title="Demo Movie",
            description="A test movie",
            genre="Drama",
            duration_minutes=100,
        )

        self.show = Show.objects.create(
            movie=self.movie,
            cinema_name="Central Cinema",
            starts_at=timezone.now() + timedelta(days=1),
            seat_capacity=3,
            ticket_price=Decimal("100.00"),
        )

        for number in range(1, 4):
            Seat.objects.create(
                show=self.show,
                seat_number=f"S{number:02d}",
            )

    def test_homepage_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_booking_requires_login(self):
        response = self.client.get(
            reverse("book_show", args=[self.show.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_booking_total_and_seat_status(self):
        self.client.login(
            username="student",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("book_show", args=[self.show.pk]),
            {"seats": ["S01", "S02"]},
        )

        self.assertEqual(response.status_code, 302)

        booking = Booking.objects.get(user=self.user)

        self.assertEqual(
            booking.total_amount,
            Decimal("200.00"),
        )

        self.assertEqual(
            Seat.objects.get(
                show=self.show,
                seat_number="S01",
            ).status,
            Seat.Status.BOOKED,
        )