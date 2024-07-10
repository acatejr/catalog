from django.urls import path
from .views import assets, MapSearchView

urlpatterns = [
    path("", assets, name="assets"),
    path("mapsearch", MapSearchView.as_view(), name="mapsearch"),
]
