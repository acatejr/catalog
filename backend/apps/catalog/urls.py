from django.urls import path, reverse
from django.views.generic import TemplateView, RedirectView
from .views import assets, MapSearchView

urlpatterns = [
    path("", assets, name="assets"),
    path("mapsearch", MapSearchView.as_view(), name="mapsearch"),
]
