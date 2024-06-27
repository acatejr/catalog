from django import forms
from django.urls import reverse


class AssetSearchForm(forms.Form):
    FULL_TEXT_SEARCH_CHOICES = [
        ("1", "Search Vector"),
        ("2", "Search Query"),
        ("3", "Search Rank"),
        ("4", "Search Headline"),
    ]

    term = forms.CharField(
        label="",
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={"id": "term", "placeholder": "search term", "class": "form-control"}
        ),
    )

    full_text_search = forms.ChoiceField(
        choices=FULL_TEXT_SEARCH_CHOICES,
        widget=forms.RadioSelect(attrs={"id": "full_text_search", "class": "checkbox"}),
        disabled=True,
    )
