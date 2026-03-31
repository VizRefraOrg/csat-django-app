from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token
from django.shortcuts import redirect

from greatcart import settings


@login_required
def home(request):
    user = request.user
    if not user.subscription or not user.subscription.status:
        messages.info(request, "Please subscribe to a plan. Start with a 10-day free trial!")
        return redirect("user_profile")
    csrf_token = get_token(request)
    return redirect(
        f"{settings.STREAMLIT_URL}?sessionid={request.session.session_key}&csrftoken={csrf_token}"
    )
