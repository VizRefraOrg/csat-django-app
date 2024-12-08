import os
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils.timezone import now


class MyAccountManager(BaseUserManager):
    def create_user(self, first_name, last_name, username, email, password=None):
        if not email:
            raise ValueError("User must have an email address")

        if not username:
            raise ValueError("User must have an username")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user


def user_profile_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    # Generate a unique filename using UUID
    filename = f'{uuid4().hex}.{ext}'
    # The uploaded file will be stored to MEDIA_ROOT/profile_photos/<user_id>/<unique_filename>
    return os.path.join('profile_photos', str(instance.id), filename)


class Account(AbstractBaseUser):
    MEMBERSHIP_CHOICES = (
        ("Free-Trial", "Free-Trial"),
        ("Monthly", "Monthly"),
        ("Annually", "Annually"),
    )

    MEMBERSHIP_STATUS_CHOICES = (
        ("Active", "Active"),
        ("Expired", "Expired"),
    )

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=100, blank=True)
    profile_photo = models.ImageField(upload_to=user_profile_photo_path, null=True, blank=True)

    # required
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)

    membership = models.CharField(max_length=50, default='', choices=MEMBERSHIP_CHOICES)
    membership_status = models.CharField(max_length=50, default='', choices=MEMBERSHIP_STATUS_CHOICES)
    membership_expiration_date = models.DateField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = MyAccountManager()

    def __str__(self):
        return self.email

    def has_perm(
        self, perm, obj=None
    ):  # This must be mentioned when creating Custom Model
        return self.is_admin

    def has_module_perms(self, add_label):
        return True

    @property
    def pricing_table(self):
        table_code = settings.STRIPE_PRICING_TABLE
        return table_code.replace('<stripe-pricing-table ', f'<stripe-pricing-table customer-email="{self.email}" ')

    @property
    def subscription(self):
        return self.subscriptions.select_related("plan").first()

    @property
    def stripe_portal(self):
        from stripe.billing_portal import Session

        if self.subscription:
            portal_session = Session.create(
                customer=self.subscription.stripe_customer_id, api_key=settings.STRIPE_SECRET_KEY
            )
            return portal_session.url


def user_directory_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/uploads/user_<id>/<timestamp>_<filename>
    timestamp = now().strftime("%Y%m%d%H%M%S")
    base, extension = os.path.splitext(filename)
    return f"uploads/user_{instance.user.id}/{timestamp}_{base}{extension}"


class UploadedFile(models.Model):
    file = models.FileField(upload_to=user_directory_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="uploaded_files"
    )

    def __str__(self):
        return self.file.name

    def get_file_url(self):
        return os.path.join(settings.MEDIA_ROOT, self.file.name)
