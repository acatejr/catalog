from django.template.defaultfilters import truncatechars
from django.db import models


class BaseModel(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Document(BaseModel):
    
    metadata_url = models.CharField(
        max_length=1500,
        unique=True,
        null=True,
        help_text="The url used to access the metadata."
    )
    
    type = models.CharField(
        max_length=150,
        unique=False,
        null=True,
        help_text="The metadata type.  Usually an ISO standard format."
    )

    description = models.CharField(
        max_length=3000,
        unique=False,
        null=True,
        help_text="The description of the metadata document.",
    )

    @property
    def short_descr(self):
        return truncatechars(self.description, 25)
