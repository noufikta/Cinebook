from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Movie, Show, Seat, Booking


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        "title", "genre", "language",
        "duration_minutes", "is_active",
    )
    list_filter = ("genre", "language", "is_active")
    search_fields = ("title", "description")


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = (
        "movie", "cinema_name", "screen_name",
        "starts_at", "seat_capacity", "ticket_price",
        "is_active",
    )
    list_filter = ("cinema_name", "is_active")
    search_fields = ("movie__title", "cinema_name")


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("show", "seat_number", "status")
    list_filter = ("status",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "booking_reference", "user", "show",
        "seat_count", "total_amount",
        "status", "payment_status",
    )
    list_filter = ("status", "payment_status")
    readonly_fields = (
        "booking_reference", "user", "show",
        "seat_count", "total_amount", "status",
        "payment_status", "created_at", "cancelled_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False