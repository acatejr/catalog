from django.urls import path, reverse
from django.views.generic import TemplateView, RedirectView
from .views import assets

urlpatterns = [
    path("", assets, name="assets"),
]
