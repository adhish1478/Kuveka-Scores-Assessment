from django.urls import path
from .views import UploadOffer, UploadLeads, RunScore, Results

urlpatterns=[
    path('offer/', UploadOffer.as_view(), name='upload_offer'),
    path('leads/upload/', UploadLeads.as_view(), name='upload_leads'),
    path('score/', RunScore.as_view(), name='run_score'),
    path('results/', Results.as_view(), name='results')
]