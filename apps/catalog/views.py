from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, filters
from rest_framework import permissions

from .models import Document
from .serializers import DocumentSerializer

class DocumentListApiView(APIView):
    """
    Returns a list of all metadata documents in the system.
    """

    def get(self, request, *args, **kwargs):
        documents = Document.objects.all()
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DocumentListView(generics.ListAPIView):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        for item in self.request.META.items():
            print(item)

        search_term = self.kwargs["search_term"]
        return Document.objects.filter(description__icontains=search_term)
