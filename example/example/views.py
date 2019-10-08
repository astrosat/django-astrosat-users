from django.shortcuts import render


def index_view(request):

    template_name = "example/index.html"
    return render(request, template_name)
