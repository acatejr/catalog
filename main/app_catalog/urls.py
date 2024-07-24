from django.urls import path
from .views import AssetSearchResults

urlpatterns = [
    path("", AssetSearchResults.as_view(), name="asset_search_results"),
]