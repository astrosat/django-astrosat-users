from django.contrib.auth.tokens import PasswordResetTokenGenerator
from allauth.account.forms import EmailAwarePasswordResetTokenGenerator


default_token_generator = EmailAwarePasswordResetTokenGenerator()
