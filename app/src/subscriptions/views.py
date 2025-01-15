# -*- coding: utf-8 -*-
import os
from datetime import datetime

import stripe
from accounts.models import Account
from django.http import JsonResponse
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt
from greatcart import settings
from loguru import logger
from stripe import StripeClient

from subscriptions.models import Subscription, SubscriptionPlan

client = StripeClient(settings.STRIPE_SECRET_KEY)


@csrf_exempt
def collect_stripe_webhook(request) -> JsonResponse:
    """
    Stripe sends webhook events to this endpoint.
    We verify the webhook signature and updates the database record.
    """
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    signature = request.META["HTTP_STRIPE_SIGNATURE"]
    payload = request.body

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=signature, secret=webhook_secret
        )
        logger.debug(event.type)
        if event.type.startswith("product."):
            status = _update_plan_record(event.data.object)
        elif event.type.startswith("customer.subscription."):
            status = _update_subscription_record(event.data.object)
        else:
            status = "not applicable"

    except ValueError as e:  # Invalid payload.
        raise e
    except stripe.error.SignatureVerificationError as e:  # Invalid signature
        raise e

    return JsonResponse({'status': status})


def _update_plan_record(product_event) -> bool:
    try:
        stripe_product = client.products.retrieve(product_event.id)
        sub_plan = SubscriptionPlan.objects.filter(stripe_product_id=stripe_product.id)
        if sub_plan:
            SubscriptionPlan.objects.update(
                name=stripe_product.name,
                type=stripe_product.active,
                # stripe_product_id=stripe_product.id,
                live_mode=stripe_product.livemode
            )
        else:
            SubscriptionPlan.objects.save(
                name=stripe_product.name,
                type=stripe_product.active,
                stripe_product_id=stripe_product.id,
                live_mode=stripe_product.livemode
            )
        return True
    except stripe._error.InvalidRequestError as e:
        logger.error(e)
        return False


def _update_subscription_record(subscription_event) -> bool:
    """
    We update our database record based on the webhook event.

    Use these events to update your database records.
    You could extend this to send emails, update user records, set up different access levels, etc.
    """

    subscription_id = subscription_event.id
    customer_id = subscription_event.customer

    try:
        customer = client.customers.retrieve(customer_id)
        subscription = client.subscriptions.retrieve(subscription_id)
        product = client.products.retrieve(subscription.plan.product)
        plan = SubscriptionPlan.objects.get(stripe_product_id=product.id)
    except stripe._error.InvalidRequestError as e:
        logger.error(e)
        return 'failed'

    user = Account.objects.get(email=customer.email)
    start = make_aware(datetime.fromtimestamp(subscription.current_period_start))
    end = make_aware(datetime.fromtimestamp(subscription.current_period_end))
    if subscription.plan.interval == 'year':
        recurring = Subscription.RecurringType.YEAR.value
    else:
        recurring = Subscription.RecurringType.MONTH.value

    status = int(subscription.status not in ['incomplete', 'incomplete_expired', 'unpaid', 'canceled', 'paused'])

    user_subscription = Subscription.objects.filter(user=user).first()
    if not user_subscription:
        Subscription.objects.create(
            user=user,
            stripe_subscription_id=subscription_id,
            stripe_customer_id=customer_id,
            stripe_status=subscription.status,
            start_at=start,
            end_at=end,
            status=status,
            plan=plan,
            recurring=recurring,
        )
    else:
        Subscription.objects.update(
            user=user,
            stripe_subscription_id=subscription_id,
            stripe_customer_id=customer_id,
            stripe_status=subscription.status,
            start_at=start,
            end_at=end,
            status=status,
            plan=plan,
            recurring=recurring,
        )
    return 'success'
