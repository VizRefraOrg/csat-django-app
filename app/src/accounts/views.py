import os
from urllib.parse import parse_qsl, urlsplit

import magic
from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator

# Account Activation
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.http.response import HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.generic import TemplateView
from loguru import logger

from .forms import RegistrationForm, UserProfileUpdateForm
from .models import Account, UploadedFile


# logger = logging.getLogger(__name__)
def heart_beat(request):
    if request.method == "GET":
        return JsonResponse({"status": "true"}, safe=False)


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            phone_number = form.cleaned_data["phone_number"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            # username = email.split("@")[0]
            user: Account = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                # phone_number=phone_number,
                username=email,
                password=password,
            )
            user.phone_number = phone_number
            user.save()

            # USER ACTIVATION
            current_site = get_current_site(request)
            mail_subject = "Please activate your account"
            message = render_to_string(
                "accounts/account_verification_email.html",
                {
                    "user": user,
                    "domain": current_site,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                },
            )
            to_email = email
            send_mail = EmailMessage(mail_subject, message, to=[to_email])
            send_mail.send()
            # messages.success(request, 'Thank you for registering with us. We have sent you a verification email to your email address. Please verify it.')
            return redirect("/accounts/login/?command=verification&email=" + email)
    else:
        form = RegistrationForm()
    context = {
        "form": form,
    }
    return render(request, "accounts/register.html", context)


def login(request):
    # logger.info(request.user)
    if request.user.is_authenticated:
        return redirect("user_profile")

    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        user = auth.authenticate(email=email, password=password)
        # logger.info(user)
        if user is not None:
            auth.login(request, user)
            # messages.success(request, "You are logged in.")
            csrf_token = get_token(request)
            # email_encode = base64.b64encode(email.encode("ascii"))
            url = request.META.get("HTTP_REFERER")
            params = dict(parse_qsl(urlsplit(url).query))
            redirect_url = params.get(b'next', settings.STREAMLIT_URL)
            # logger.info(request.session.session_key)
            # logger.info(csrf_token)
            # logger.info(redirect_url)

            if user.subscription and user.subscription.status:
                return redirect(
                    f"{redirect_url}?sessionid={request.session.session_key}&csrftoken={csrf_token}"
                )
            else:
                messages.info(request, "Please subscribe a plan. You could have 3 days trial!")
                return redirect("user_profile")
        else:
            messages.error(request, "Invalid login credentials")
            return redirect("login")
    # elif request.method == "GET":
    #     logger.info(request.body.decode('utf-8'))

    return render(request, "accounts/login.html")


@login_required(login_url="login")
def logout(request):
    auth.logout(request)
    # messages.success(request, str(request.user))
    messages.success(request, "You are logged out.")
    return redirect("login")


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TabError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Congratulations! Your Account is Activated.")
        return redirect("login")
    else:
        messages.error(request, "Invalid Activation Link")
        return redirect("register")


def forgot_password(request):
    if request.method == "POST":
        email = request.POST["email"]
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # RESET PASSWORD EMAIL
            current_site = get_current_site(request)
            mail_subject = "Reset Your Password"
            message = render_to_string(
                "accounts/reset_password_email.html",
                {
                    "user": user,
                    "domain": current_site,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                },
            )
            to_email = email
            send_mail = EmailMessage(mail_subject, message, to=[to_email])
            send_mail.send()

            messages.success(
                request, "Password reset email has been sent to your address."
            )
            return redirect("login")
        else:
            messages.error(request, "Account Does Not Exists!")
            return redirect("forgotPassword")
    return render(request, "accounts/forgotPassword.html")


def reset_password_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TabError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session["uid"] = uid
        messages.success(request, "Please reset your password")
        return render(request, "accounts/resetPassword.html")
    else:
        messages.error(request, "This Link has been expired")
        return redirect("login")


def reset_password(request):
    if request.method == "POST":
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        try:
            uid = request.session.get('uid')
            user = Account._default_manager.get(pk=uid)
        except (TabError, ValueError, OverflowError, Account.DoesNotExist):
            user = None

        if not user:
            messages.error(request, "Cannot reset your password!")
            return redirect("login")
        elif password == confirm_password:
            user.set_password(password)
            user.save()
            messages.success(request, "Password reset successful")
            return redirect("login")
        else:
            messages.error(request, "Password do not match")
            return redirect("resetPassword")

    return render(request, "accounts/resetPassword.html")


class FileUploadView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        file = request.FILES.get("file")
        if not file:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        try:
            # Save the file to the model
            uploaded_file = UploadedFile.objects.create(file=file, user=request.user)
            logger.info(f"File saved: {uploaded_file.file.path}")

            return JsonResponse(
                {
                    "id": uploaded_file.id,
                    "file": uploaded_file.file.name,
                    "uploaded_at": uploaded_file.uploaded_at,
                    "file_url": uploaded_file.get_file_url(),
                    "user": uploaded_file.user.username,
                },
                status=201,
            )
        except Exception as e:
            logger.error(f"File processing error: {e}")
            return JsonResponse({"error": "Failed to process the file"}, status=500)


@login_required(login_url="login")
def list_user_files(request):
    # logger.info(request.user)
    user_files = UploadedFile.objects.filter(user=request.user)
    files_data = [
        {
            "id": file.id,
            "file_name": os.path.basename(file.file.name),
            "uploaded_at": file.uploaded_at,
            "file_path": file.file.path,
            "file_size": file.file_size,
            "checksum": file.file_checksum
        }
        for file in user_files if os.path.exists(file.file.path)
    ]
    return JsonResponse(files_data, safe=False)


class SelectFileView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        file_path = request.POST.get('file_path')
        if file_path is None:
            return JsonResponse({"error": "file_path is required in request body"}, status=400)
        elif not os.path.exists(file_path):
            return JsonResponse({"error": "file_path doesn't exist"}, status=400)
        else:
            content_type = magic.from_file(file_path, mime=True)
            file_to_send = ContentFile(open(file_path, "rb").read())
            response = HttpResponse(file_to_send, content_type)
            response['Content-Length'] = file_to_send.size
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response


class UserProfileView(LoginRequiredMixin, TemplateView):
    login_url = 'login'
    template_name = "accounts/user_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = self.request.user
        context["current_user"] = current_user
        context["form"] = UserProfileUpdateForm(instance=current_user)
        context["analysis_url"] = settings.STREAMLIT_URL
        context["pricing_table_id"] = settings.STRIPE_PRICING_TABLE_ID
        context["public_key"] = settings.STRIPE_PUBLIC_KEY
        return context

    def post(self, request, *args, **kwargs):
        current_user = self.request.user

        form = UserProfileUpdateForm(request.POST, request.FILES, instance=current_user)
        if form.is_valid():
            form.save()
            messages.success(request, "User profile updated successfully!")
            return redirect("user_profile")
        else:
            context = self.get_context_data(**kwargs)
            context["form"] = form
            return self.render_to_response(context)


@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('login')

    return render(request, 'accounts/delete_account.html')


@login_required
def redirect_to_analysis(request):
    user = request.user
    if not user.subscription or not user.subscription.status:
        return redirect("user_profile")

    csrf_token = get_token(request)
    url = request.META.get("HTTP_REFERER")
    try:
        params = dict(parse_qsl(urlsplit(url).query))
        redirect_url = params.get(b'next', settings.STREAMLIT_URL)
        return redirect(
            f"{redirect_url}?sessionid={request.session.session_key}&csrftoken={csrf_token}"
        )
    except Exception as e:
        logger.error(e)
        return redirect(
            f"{settings.STREAMLIT_URL}?sessionid={request.session.session_key}&csrftoken={csrf_token}"
        )


@login_required(login_url='login')
def redirect_to_stripe(request):
    user = request.user
    if not user.subscription:
        return redirect("user_profile")

    return redirect(user.stripe_portal(return_url=request.META.get("HTTP_REFERER")))
