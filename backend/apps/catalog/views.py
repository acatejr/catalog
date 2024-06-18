from django.shortcuts import render
from django.views.generic import TemplateView, FormView, ListView
from django.db.models import Q
from django.core.paginator import Paginator
from .forms import SimpleSearchForm
from .models import Asset

def simple_search(request, term=None, page=1):
    template = "simple_search.html"
    
    if request.method == "GET":
        
        if "term" in request.GET.keys():
            term = request.GET.get("term")

        if term:
            assets = Asset.objects.filter(Q(description__icontains=term) | Q(title__icontains=term)).order_by("id")
            paginator = Paginator(assets, 15)               
            assets = paginator.page(page)
            return render(request, template, {"term": term, "page": page, "assets": assets})

        return render(request, template, {"term": term, "page": page})

class AssetListView(ListView):
    model = Asset
    paginate_by = 25
    context_object_name = "assets"
    ordering = ["title", "description"]
