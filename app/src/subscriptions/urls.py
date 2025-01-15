# -*- coding: utf-8 -*-
from django.urls import path

# from subscriptions.views import SubscriptionViewSet
from . import views

urlpatterns = [
    path("webhook", views.collect_stripe_webhook, name="webhook")
]
