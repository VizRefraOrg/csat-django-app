from django.urls import path

from . import views

urlpatterns = [
    path("heartbeat", views.heart_beat, name="heartbeat"),
    path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("/", views.dashboard, name="dashboard"),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    path("forgotPassword/", views.forgotPassword, name="forgotPassword"),
    path(
        "resetpassword_validate/<uidb64>/<token>/",
        views.resetpassword_validate,
        name="resetpassword_validate",
    ),
    path("resetPassword/", views.resetPassword, name="resetPassword"),
    path("select_file/", views.SelectFileView.as_view(), name="select_file"),
    path("upload_file/", views.FileUploadView.as_view(), name="upload_file"),
    path("list_user_files/", views.list_user_files, name="list_user_files"),
    path("user-profile/", views.UserProfileView.as_view(), name="user_profile"),
    path("delete-account/", views.delete_account, name="delete-account"),
    path("redirect-to-analysis/", views.redirect_to_analysis, name="redirect-to-analysis"),
    path("redirect-to-stripe/", views.redirect_to_stripe, name="redirect-to-stripe")
]
