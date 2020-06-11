from .views_tokens import token_view
from .views_auth import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetView,
    PasswordResetConfirmView,
    RegisterView,
    VerifyEmailView,
    SendEmailVerificationView,
)
from .views_customers import CustomerDetailView, CustomerUserListView, CustomerUserDetailView
from .views_users import UserViewSet, UserListView, UserDetailView, UserUpdateView
from .views_messages import message_view
