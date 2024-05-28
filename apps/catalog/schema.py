import graphene
from graphene_django import DjangoObjectType
from django.db.models import Q
from apps.catalog.models import Document


class DocumentType(DjangoObjectType):
    class Meta:
        model = Document
        fields = ("id", "description")


class Query(graphene.ObjectType):
    health = graphene.String(default_value="ok")
    all_documents = graphene.List(DocumentType)
    document_by_search_term = graphene.List(
        DocumentType, term=graphene.String(required=True)
    )

    def resolve_all_documents(root, info):
        return Document.objects.all()

    def resolve_document_by_search_term(root, info, term):
        try:
            # Q(title__icontains=term) | Q(description__icontains=term)                                                                                                |▸ mmp/
            object_list = Document.objects.filter(Q(description__icontains=term))
            return object_list

        except Document.DoesNotExist:
            return None


schema = graphene.Schema(query=Query)
