from django.urls import path
from django.views.generic import TemplateView
from .views import AssetListView, simple_search, AdvancedSearch

urlpatterns = [
    path("assets", AssetListView.as_view(), name="assets"),
    path(
        "assets/simplesearch/<str:term>/<int:page>",
        view=simple_search,
        name="simple_search",
    ),
    path("assets/simplesearch", view=simple_search),
    path(
        "assets/advancedsearch", view=AdvancedSearch.as_view(), name="advanced_search"
    ),
]
