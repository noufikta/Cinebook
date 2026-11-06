from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),

    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="booking/form.html",
            extra_context={"heading": "Log in"},
        ),
        name="login",
    ),

    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("movies/<int:movie_id>/", views.movie_detail, name="movie_detail"),
    path("shows/<int:show_id>/book/", views.book_show, name="book_show"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path("tickets/<int:booking_id>/", views.ticket, name="ticket"),
    path(
        "bookings/<int:booking_id>/cancel/",
        views.cancel_booking,
        name="cancel_booking",
    ),
]