from django.shortcuts import render
from django.views.generic import ListView
from django.views.generic.edit import FormMixin
from django.db.models import Q

from .models import Asset, SearchTerm
from .forms import AssetSimpleSerchForm


class AssetSearchResults(ListView, FormMixin):
    model = Asset
    context_object_name = "asset_list"
    template_name = "catalog/asset_search_results.html"
    paginate_by = 13
    form_class = AssetSimpleSerchForm
    search_term = None

    def get_context_data(self, **kwargs):
        context = super(AssetSearchResults, self).get_context_data(**kwargs)
        return context

    def get_queryset(self):
        if self.search_term:
            qs = Asset.objects.filter(
                Q(title__icontains=self.search_term)
                | Q(description__icontains=self.search_term)
            ).order_by("title")
        else:
            qs = Asset.objects.all()

        return qs

    def get(self, request, *args, **kwargs):
        if self.request.GET:
            frm = AssetSimpleSerchForm(self.request.GET)
            if frm.is_valid():
                self.search_term = frm.cleaned_data["search_term"]
                st = SearchTerm(term=self.search_term)
                st.save()

        self.object_list = self.get_queryset().order_by("title")
        context = self.get_context_data()

        return self.render_to_response(context)
