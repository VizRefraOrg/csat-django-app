# -*- coding: utf-8 -*-
import time as t
from datetime import datetime

from accounts.models import Account
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from stripe import AuthenticationError, InvalidRequestError, StripeClient

from subscriptions.models import Subscription, SubscriptionPlan


class SubscriptionViewSet(viewsets.GenericViewSet):
    authentication_classes = []  # disables authentication
    permission_classes = []  # disables permission

    @action(detail=False, methods=['post'], url_name='subscription', url_path='subscription')
    def subscription(self, request):
        # Wait 10 seconds before check
        t.sleep(10)
        try:
            client = StripeClient(settings.STRIPE_SECRET_KEY)

            subscription_id = request.data['data']['object']['id']
            customer_id = request.data['data']['object']['customer']

            customer = client.customers.retrieve(customer_id)
            subscription = client.subscriptions.retrieve(subscription_id)

            user = Account.objects.get(email=customer.email)
            plan = SubscriptionPlan.objects.get(stripe_product_id=subscription.plan.product)

            start = datetime.fromtimestamp(subscription.current_period_start)
            end = datetime.fromtimestamp(subscription.current_period_end)

            user_subscription = Subscription.objects.filter(user=user).first()

            if request.data['data']['object']['plan']['interval'] == 'year':
                recurring = Subscription.RecurringType.YEAR.value
            else:
                recurring = Subscription.RecurringType.MONTH.value

            try:
                ['incomplete_expired', 'unpaid', 'canceled', 'paused'].index(subscription.status)
                status = 0
            except ValueError:
                status = 1

            if user_subscription:
                user_subscription.start_at = start
                user_subscription.end_at = end
                user_subscription.plan = plan
                user_subscription.status = status
                user_subscription.stripe_subscription_id = subscription_id
                user_subscription.stripe_customer_id = customer_id
                user_subscription.recurring = recurring
                user_subscription.save()
            else:
                Subscription.objects.create(
                    user=user,
                    stripe_subscription_id=subscription_id,
                    stripe_customer_id=customer_id,
                    start_at=start,
                    end_at=end,
                    status=status,
                    plan=plan,
                    recurring=recurring,
                )

            return Response(True, status=200)
        except (AuthenticationError, InvalidRequestError, Account.DoesNotExist, SubscriptionPlan.DoesNotExist, ValueError) as error:
            print("Error: ", error)
            return Response(False, status=200)
