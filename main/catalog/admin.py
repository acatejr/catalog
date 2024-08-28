from django.contrib import admin
from .models import Domain, Asset, Keyword, SearchTerm, AssetKeyword


class KeywordsInline(admin.TabularInline):
    model = Keyword.assets.through


class AssetInline(admin.TabularInline):
    model = Asset
    fields = ["title"]

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    ordering = ["pk"]
    inlines = [AssetInline]
    list_display = ["id", "name", "root_domain"]


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    ordering = ["pk"]
    list_display = ["id", "title", "domain", "short_descr"]
    list_filter = ["domain"]
    inlines = [KeywordsInline]
    list_per_page = 20


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    ordering = ["word"]
    list_display = ["id", "word"]
    list_per_page = 25


@admin.register(SearchTerm)
class SearchTermAdmin(admin.ModelAdmin):
    ordering = ["pk"]
    list_display = [
        "id",
        "term",
    ]
