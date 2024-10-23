# -*- coding: utf-8 -*-
from django.contrib import admin

from subscriptions.models import Subscription, SubscriptionPlan


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'plan', 'start_at', 'end_at')
    list_filter = ('user', 'status', 'stripe_subscription_id', 'stripe_customer_id', 'start_at', 'end_at')
    readonly_fields = (
        'id',
        'user',
        'stripe_subscription_id',
        'stripe_customer_id',
        'status',
        'plan',
        'start_at',
        'end_at',
    )
    ordering = ('-start_at',)
    search_fields = ('stripe_subscription_id', 'stripe_customer_id')


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'stripe_product_id', 'type')
    list_filter = ('name', 'stripe_product_id', 'type')
    readonly_fields = ('id', )
    ordering = ('-name',)
    search_fields = ('name', 'stripe_product_id')
