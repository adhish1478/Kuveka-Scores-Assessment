from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from . import utils
# Create your views here.
OFFER = {}
LEADS = []
SCORED_RESULTS = 0

class UploadOffer(APIView):
    """Accept JSON offer details and store in memory"""
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
    
class UploadLeads(APIView):
    """Accept CSV file and parse leads"""
    def post(self, request):
        global LEADS
        if "file" not in request.FILES:
            return Response({"error": "CSV file required"}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES["file"]
        LEADS= utils.parse_leads_csv(file)
        return Response({"message": f"{len(LEADS)} leads uploaded successfully", "leads": LEADS}, status=status.HTTP_201_CREATED)

class RunScore(APIView):
    """Run scoring pipeline"""
    def post(self, request):
        global SCORED_RESULTS
        if not OFFER or not LEADS:
            return Response({"error": "Upload offer and leads first"}, status=status.HTTP_400_BAD_REQUEST)
        SCORED_RESULTS= utils.final_score(LEADS, OFFER)
        return Response({"message": "Scoring complete", "count": SCORED_RESULTS}, status=status.HTTP_200_OK)

class Results(APIView):
    """Get Scored Results"""
    def get(self, request):
        global SCORED_RESULTS
        if not SCORED_RESULTS:
            return Response({"error": "No results found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"results": SCORED_RESULTS}, status=status.HTTP_200_OK)