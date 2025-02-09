# -*- coding: utf-8 -*-
from accounts.models import Account
from django.db import models


class SubscriptionPlan(models.Model):
    """
    SubscriptionPlan model
    """

    name = models.CharField(max_length=255)
    stripe_product_id = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=255, db_index=True, null=True)
    live_mode = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_plan'
        verbose_name = 'Subscription plan'

    verbose_name_plural = 'Subscription plans'

    def __str__(self):
        return self.name


class Subscription(models.Model):
    class Statuses(models.IntegerChoices):
        ACTIVE = 1, 'Active'
        INACTIVE = 0, 'Inactive'

    class RecurringType(models.IntegerChoices):
        MONTH = 0, 'Month'
        YEAR = 1, 'Year'

    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="subscriptions", null=False)
    stripe_subscription_id = models.TextField(db_index=True)
    stripe_customer_id = models.TextField(db_index=True)
    stripe_status = models.TextField(null=True)
    status = models.IntegerField(choices=Statuses.choices, default=Statuses.INACTIVE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, null=False)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    recurring = models.IntegerField(choices=RecurringType.choices, default=RecurringType.MONTH)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.status)

    class Meta:
        db_table = 'subscription'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
