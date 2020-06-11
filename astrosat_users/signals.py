import django.dispatch


from allauth.account.signals import password_changed


# note I am not using signals for any of the custom authentication stuff,
# instead I use a custom adapter, so that needless code doesn't run when interacting via the shell


#############
# customers #
#############

customer_added_user = django.dispatch.Signal(providing_args=["customer", "user"])
customer_removed_user = django.dispatch.Signal(providing_args=["customer", "user"])
