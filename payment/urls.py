from django.urls import path
from . import views


# urls.py
urlpatterns = [
    path("webhooks/paystack/", views.paystack_webhook, name="paystack_webhook"),
]
