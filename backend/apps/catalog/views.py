from django.shortcuts import render
from django.views.generic import TemplateView, FormView, ListView
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
# from .forms import SimpleSearchForm, AdvancedSearchForm
from .forms import AssetSearchForm
from .models import Asset, SearchTerm

class AssetSearchFormView(FormView):
    model = Asset
    form_class = AssetSearchForm
    template_name = "asset_search.html"

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""    
        context = self.get_context_data()
        if "term" in self.request.GET.keys():
            term = request.GET["term"]
            search_term = SearchTerm(term=term)
            search_term.save()
            assets = Asset.objects.filter(
                Q(description__icontains=term) | Q(title__icontains=term)
            ).order_by("id")
            context["assets"] = assets

        return self.render_to_response(context)


def simple_search(request, term=None, page=1):
    template = "simple_search.html"

    if request.method == "GET":
        if "term" in request.GET.keys():
            term = request.GET.get("term")

        if term:
            search_term = SearchTerm(term=term)
            search_term.save()
            assets = Asset.objects.filter(
                Q(description__icontains=term) | Q(title__icontains=term)
            ).order_by("id")
            paginator = Paginator(assets, 15)
            assets = paginator.page(page)
            return render(
                request, template, {"term": term, "page": page, "assets": assets}
            )

        return render(request, template, {"term": term, "page": page})


class AdvancedSearch(ListView):
    model = Asset
    template_name = "advanced_search.html"
    context_object_name = "assets"
    ordering = ["title", "description"]
    paginate_by = 15
    term = ""
    success_url = "foo"

    def get(self, request, *args, **kwargs):
        self.object_list = Asset.objects.none()
        context = self.get_context_data(*args, **kwargs)
        assets = Asset.objects.none()
        if "term" in self.request.GET.keys():
            self.term = self.request.GET["term"]            
            if self.term:
                search_term = SearchTerm(term=self.term)
                search_term.save()
                search_vector = SearchVector("title", "description")
                search_query = SearchQuery(self.term)
                assets = (
                    Asset.objects.annotate(
                        search=search_vector,
                        rank=SearchRank(search_vector, search_query),
                    )
                    .filter(search=self.term)
                    .order_by("-rank")
                )
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
