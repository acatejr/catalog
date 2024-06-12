from django.contrib import admin

from django.contrib import admin
from .models import Domain, RootDomain


@admin.register(RootDomain)
class RootDomainAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "created_on", "updated_on"]

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "created_on", "updated_on"]


# from django.contrib import admin
# from django import forms
# from .models import Document


# @admin.register(Document)
# class DocumentAdmin(admin.ModelAdmin):
#     list_display = ["id", "short_descr", "created_on", "updated_on"]

#     def get_form(self, request, obj=None, **kwargs):
#         kwargs["widgets"] = {
#             "description": forms.Textarea(attrs={"rows": 10, "cols": 100})
#         }
#         return super().get_form(request, obj, **kwargs)
