# -*- coding: utf-8 -*-
from rest_framework.routers import DefaultRouter

from subscriptions.views import SubscriptionViewSet

router = DefaultRouter()
router.register('stripe', SubscriptionViewSet, basename='stripe_webhooks')
urlpatterns = router.urls
