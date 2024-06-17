from django.urls import path
from django.views.generic import TemplateView
from .views import simple_search

urlpatterns = [
    path("", view=simple_search, name="simple_search"),
]