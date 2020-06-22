from django.core.exceptions import ValidationError

from zxcvbn import zxcvbn


#######################
# password validation #
#######################


class LengthPasswordValidator:
    """
    Validates the password length is inside a range.
    """

    def __init__(self, min_length=8, max_length=255):
        assert (
            max_length > min_length and min_length >= 1 and max_length <= 255
        ), "Invalid LengthPasswordValidator"
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, password, user=None):

        password_length = len(password)

        if password_length < self.min_length:
            raise ValidationError(
                f"This password is too short.  It must contain at least {self.min_length} characters",
                code="password_too_short",
            )

        elif password_length > self.max_length:
            raise ValidationError(
                f"This password is too long.  It must contain at most {self.max_length} characters",
                code="password_too_long",
            )

    def get_help_text(self):
        return f"The password must contain between {self.min_length} and {self.max_length} characters."


class StrengthPasswordValidator:
    """
    Validates a password using the zxcvbn strength estimator.
    strength is set in __init__; possible values are:
        0 # too guessable: risky password. (guesses < 10^3)
        1 # very guessable: protection from throttled online attacks. (guesses < 10^6)
        2 # somewhat guessable: protection from unthrottled online attacks. (guesses < 10^8)
        3 # safely unguessable: moderate protection from offline slow-hash scenario. (guesses < 10^10)
        4 # very unguessable: strong protection from offline slow-hash scenario. (guesses >= 10^10)
    """

    def __init__(self, strength=2):
        assert 0 <= strength <= 4, "Invaid StrongPasswordValidator strength."
        self.strength = strength

    def validate(self, password, user=None):

        user_inputs = [user.email, user.username, user.name] if user is not None else []

        password_results = zxcvbn(password, user_inputs=user_inputs)

        if password_results["score"] < self.strength:
            error_msg = password_results["feedback"]["warning"]
            error_msg += "; ".join(password_results["feedback"]["suggestions"])
            raise ValidationError(error_msg, code="password_too_weak")

    def get_help_text(self):
        return f"The password must be strong."
