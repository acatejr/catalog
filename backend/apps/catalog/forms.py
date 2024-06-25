from django import forms
from django.urls import reverse

class AssetSearchForm(forms.Form):

    term = forms.CharField(
        label="",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'search term'})
    )

    # full_text_search = forms.BooleanField()



# class SimpleSearchForm(forms.Form):
#     search_term = forms.CharField(
#         label="",
#         max_length=150,
#         required=True,
#     )

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.form_id = "simple-search"
#         self.helper.form_class = "form"
#         self.helper.form_method = "get"
#         self.helper.form_action = reverse("simple_search")

#         self.helper.add_input(Submit("submit", "Search"))


# class AdvancedSearchForm(forms.Form):
#     term = forms.CharField(
#         label="",
#         max_length=150,
#         required=True,
#     )

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.form_id = "simple-search"
#         self.helper.form_class = "form"
#         self.helper.form_method = "get"
#         self.helper.form_action = reverse("advanced_search")

#         self.helper.add_input(Submit("submit", "Search"))
