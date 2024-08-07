from django.shortcuts import render
from django.views.generic import TemplateView, ListView

from .models import Asset

class AssetSearchResults(ListView):
    model = Asset
    context_object_name = "asset_list"
    template_name = 'app_catalog/asset_search_results.html'
    paginate_by = 20
