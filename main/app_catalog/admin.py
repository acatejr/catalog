from django.contrib import admin
from .models import Domain, Asset, SearchTerm


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    ordering = ["pk"]
    list_display = ["id", "name"]

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    ordering = ["pk"]
    list_display = ["id", "title", "short_descr"]

@admin.register(SearchTerm)
class SearchTermAdmin(admin.ModelAdmin):
    ordering = ["pk"]
    list_display = ["id", "term",]