from django.template.defaultfilters import truncatechars
from django.db import models

class BaseModel(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Document(BaseModel):
    
    description = models.CharField(
        max_length=3000,
        unique=False,
        null=True,
        help_text="The description of the metadata document.",
    )

    @property
    def short_descr(self):
        return truncatechars(self.description, 25)

