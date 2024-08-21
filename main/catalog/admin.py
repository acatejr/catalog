from django.contrib import admin
from .models import Domain, Asset, Keyword, SearchTerm


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    ordering = ["pk"]
    list_display = ["id", "name", "root_domain"]


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    ordering = ["pk"]
    list_display = ["id", "title", "domain", "short_descr"]
    list_filter = ["domain"]
    list_per_page = 20


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    ordering = ["pk"]
    list_display = ["id", "word", "asset"]


@admin.register(SearchTerm)
class SearchTermAdmin(admin.ModelAdmin):
    ordering = ["pk"]
    list_display = [
        "id",
        "term",
    ]
