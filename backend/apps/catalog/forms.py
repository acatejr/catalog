from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.urls import reverse

class SimpleSearchForm(forms.Form):

    search_term = forms.CharField(
        label = "",
        max_length = 150,
        required = True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'simple-search'
        self.helper.form_class = 'form'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse("simple_search")

        self.helper.add_input(Submit('submit', 'Search'))