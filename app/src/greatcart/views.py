from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from greatcart import settings


@login_required
def home(request):
    return redirect(settings.STREAMLIT_URL)
