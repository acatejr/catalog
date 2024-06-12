from django import forms
from django.contrib import admin
from .models import Domain, RootDomain, Asset


@admin.register(RootDomain)
class RootDomainAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "description", "created_on", "updated_on"]

    def get_form(self, request, obj=None, **kwargs):
        kwargs["widgets"] = {
            "description": forms.Textarea(attrs={"rows": 10, "cols": 100})
        }
        return super().get_form(request, obj, **kwargs)


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "short_descr", "created_on", "updated_on"]


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "short_url", "short_descr", "created_on", "updated_on"]

    def get_form(self, request, obj=None, **kwargs):
        kwargs["widgets"] = {
            "description": forms.Textarea(attrs={"rows": 10, "cols": 100})
        }
        return super().get_form(request, obj, **kwargs)
