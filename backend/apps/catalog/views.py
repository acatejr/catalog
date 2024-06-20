from django.shortcuts import render
from django.views.generic import TemplateView, FormView, ListView
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchVector
from .forms import SimpleSearchForm, AdvancedSearchForm
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


class AdvancedSearch(ListView):
    model = Asset
    template_name = "advanced_search.html"
    context_object_name = "assets"
    ordering = ["title", "description"]
    paginate_by = 15
    term = ""

    def get(self, request, *args, **kwargs):
        self.object_list = Asset.objects.all().order_by("id")
        context = self.get_context_data(*args, **kwargs)       
        assets = Asset.objects.none()
        if "term" in self.request.GET.keys():
            self.term = self.request.GET["term"]
            if self.term:
                assets = Asset.objects.annotate(
                    search=SearchVector("title", "description"),
                ).filter(search=self.term)
                context["assets"] = assets
            else:                
                context["assets"] = assets

        return render(request, self.template_name, context)

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['form'] = AdvancedSearchForm()
    #     return context


class AssetListView(ListView):
    model = Asset
    paginate_by = 25
    context_object_name = "assets"
    ordering = ["title", "description"]
