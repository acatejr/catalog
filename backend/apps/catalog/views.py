from django.shortcuts import render
from django.views.generic import TemplateView, FormView, ListView
from django.views.generic.edit import FormMixin
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import AssetSearchForm
from .models import Asset, SearchTerm
from django.http import HttpResponse
from django.views import View


def assets(request):
    template = "catalog/asset_list.html"
    form = AssetSearchForm()
    context = {"form": form}
    items_per_page = 15

    if request.method == "GET":
        if "term" in request.GET.keys():
            term = request.GET.get("term")
            if term:
                search_term = SearchTerm(term=term)
                search_term.save()
                items = Asset.objects.filter(
                    Q(description__icontains=term) | Q(title__icontains=term)
                ).order_by("id")
        else:
            items = Asset.objects.all().order_by("id")

        page = request.GET.get("page", 1)
        paginator = Paginator(items, items_per_page)
        try:
            assets = paginator.page(page)
        except PageNotAnInteger:
            assets = paginator.page(1)
        except EmptyPage:
            assets = paginator.page(paginator.num_pages)

    context["assets"] = assets
    return render(request, template, context)



class MapSearchView(View):
    template_name = "catalog/map_search.html"

    def get(self, request, *args, **kwargs):

        return render(request, self.template_name, {"form": None})
