from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from . import utils
# Create your views here.
OFFER = {}
LEADS = []
SCORED_RESULTS = []

class UploadOffer(APIView):
    def post(self, request):
        global OFFER
        OFFER.clear()
        OFFER.update(request.data)
        return Response(
            {
                "message": "Offer uploaded successfully",
                "offer": OFFER
            },
            status=status.HTTP_201_CREATED
)