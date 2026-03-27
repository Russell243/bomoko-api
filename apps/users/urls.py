from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    UserProfileView,
    VerifyOTPView,
    ChangePasswordView,
    DeactivateAccountView,
    DeleteAccountView,
)

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('deactivate/', DeactivateAccountView.as_view(), name='deactivate_account'),
    path('delete/', DeleteAccountView.as_view(), name='delete_account'),
]
