from django.http import JsonResponse
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import login
from django.contrib.auth.models import User
import json

GOOGLE_CLIENT_ID = "163047147866-bglvumvpnd3g9fuppk4vh02ld19i5pvk.apps.googleusercontent.com"

def google_auth_callback(request):
    try:
        data = json.loads(request.body)
        token = data.get("token")

        if not token:
            return JsonResponse({"success": False, "error": "No token provided"}, status=400)

        # Verify token
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

        if "email" in idinfo:
            email = idinfo["email"]
            name = idinfo.get("name", "")

            # Check if user exists, else create new user
            user, created = User.objects.get_or_create(username=email, email=email)
            if created:
                user.first_name = name.split()[0]
                user.set_unusable_password()
                user.save()

            login(request, user)
            return JsonResponse({"success": True, "redirect": "/dashboard/"})

        return JsonResponse({"success": False, "error": "Invalid token"}, status=401)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
