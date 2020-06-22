from django.views.generic import TemplateView

from astrosat_users.models import User, Customer


class IndexView(TemplateView):

    template_name = "example/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = User.objects.filter(is_active=True)
        context["customers"] = Customer.objects.filter(is_active=True)
        return context
