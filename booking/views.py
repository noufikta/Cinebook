from django.shortcuts import render

# Create your views here.
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .forms import RegistrationForm, BookingForm
from .models import Movie, Show, Seat, Booking


def home(request):
    movies = Movie.objects.filter(is_active=True)

    shows = Show.objects.filter(
        is_active=True,
        starts_at__gte=timezone.now(),
        movie__is_active=True,
    ).select_related("movie")[:8]

    return render(
        request,
        "booking/home.html",
        {"movies": movies, "shows": shows},
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = RegistrationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Account created.")
        return redirect("home")

    return render(
        request,
        "booking/form.html",
        {"form": form, "heading": "Create account"},
    )


def movie_detail(request, movie_id):
    movie = get_object_or_404(
        Movie, pk=movie_id, is_active=True
    )

    shows = movie.shows.filter(
        is_active=True,
        starts_at__gte=timezone.now(),
    ).order_by("starts_at")

    return render(
        request,
        "booking/movie.html",
        {"movie": movie, "shows": shows},
    )


@login_required
def book_show(request, show_id):
    show = get_object_or_404(
        Show.objects.select_related("movie"),
        pk=show_id,
        is_active=True,
        movie__is_active=True,
    )

    if show.starts_at <= timezone.now():
        messages.error(
            request,
            "Bookings are closed for a show that has started.",
        )
        return redirect("movie_detail", movie_id=show.movie_id)

    # Provision seats once per show.
    if not show.seats.exists():
        try:
            with transaction.atomic():
                for number in range(1, show.seat_capacity + 1):
                    Seat.objects.get_or_create(
                        show=show,
                        seat_number=f"S{number:02d}",
                    )
        except IntegrityError:
            pass

    form = BookingForm(request.POST or None, show=show)

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                locked_show = Show.objects.select_for_update().get(
                    pk=show.pk
                )

                selected = list(
                    Seat.objects.select_for_update().filter(
                        show=locked_show,
                        seat_number__in=form.cleaned_data["seats"],
                        status=Seat.Status.AVAILABLE,
                    ).order_by("seat_number")
                )

                if len(selected) != len(form.cleaned_data["seats"]):
                    raise ValidationError(
                        "A selected seat was just booked. Refresh and select again."
                    )

                total = (
                    locked_show.ticket_price * Decimal(len(selected))
                ).quantize(Decimal("0.01"))

                booking = Booking.objects.create(
                    user=request.user,
                    show=locked_show,
                    seat_count=len(selected),
                    total_amount=total,
                    status=Booking.Status.CONFIRMED,
                    payment_status=Booking.PaymentStatus.PAID,
                )

                booking.seats.set(selected)

                Seat.objects.filter(
                    pk__in=[seat.pk for seat in selected]
                ).update(status=Seat.Status.BOOKED)

            messages.success(
                request,
                "Simulated payment successful. Ticket confirmed.",
            )

            return redirect("ticket", booking_id=booking.pk)

        except ValidationError as error:
            form.add_error("seats", error)

        except IntegrityError:
            form.add_error(
                None,
                "Availability changed. Please try again.",
            )

    return render(
        request,
        "booking/seats.html",
        {"show": show, "form": form, "seats": show.seats.all()},
    )


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(
        user=request.user
    ).select_related(
        "show", "show__movie"
    ).prefetch_related("seats")

    return render(
        request,
        "booking/bookings.html",
        {"bookings": bookings},
    )


@login_required
def ticket(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related(
            "show", "show__movie", "user"
        ).prefetch_related("seats"),
        pk=booking_id,
        user=request.user,
    )

    return render(
        request,
        "booking/ticket.html",
        {"booking": booking},
    )


@login_required
def cancel_booking(request, booking_id):
    if request.method != "POST":
        return redirect("my_bookings")

    with transaction.atomic():
        booking = Booking.objects.select_for_update().filter(
            pk=booking_id,
            user=request.user,
        ).first()

        if not booking:
            raise Http404

        if booking.status != Booking.Status.CONFIRMED:
            messages.error(request, "Booking already cancelled.")

        elif booking.show.starts_at <= timezone.now():
            messages.error(
                request,
                "Cannot cancel after the show starts.",
            )

        else:
            seats = list(booking.seats.select_for_update())

            booking.status = Booking.Status.CANCELLED
            booking.payment_status = Booking.PaymentStatus.REFUNDED
            booking.cancelled_at = timezone.now()

            booking.save(
                update_fields=[
                    "status",
                    "payment_status",
                    "cancelled_at",
                ]
            )

            Seat.objects.filter(
                pk__in=[seat.pk for seat in seats]
            ).update(status=Seat.Status.AVAILABLE)

            messages.success(
                request,
                "Booking cancelled; simulated refund recorded.",
            )

    return redirect("my_bookings")