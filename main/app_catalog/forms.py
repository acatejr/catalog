from django import forms


class AssetSimpleSerchForm(forms.Form):
    search_term = forms.CharField(
        label="Search Term", widget=forms.TextInput(attrs={"class": "form-control"})
    )
