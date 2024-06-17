from django.shortcuts import render
from django.views.generic import TemplateView, FormView
from django.db.models import Q
from .forms import SimpleSearchForm
from .models import Asset

def simple_search(request):
    template = "simple_search.html"
    data = None

    if request.method == "GET":
        return render(request, template, {"form": SimpleSearchForm()})
    elif request.method == "POST":
        form = SimpleSearchForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            search_term = cleaned_data["search_term"]
            assets = Asset.objects.filter(Q(description__icontains=search_term) | Q(title__icontains=search_term))
            if assets:
                data = {
                    "assets": assets
                }

        return render(request, template, {"form": SimpleSearchForm(), "data": data})


class SimpleSearchView(FormView):
    form_class = SimpleSearchForm
    template_name = "catalog/simple_search.html"
