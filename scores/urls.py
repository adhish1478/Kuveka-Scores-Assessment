from django.urls import path
from .views import UploadOffer

urlpatterns=[
    path('offer/', UploadOffer.as_view(), name='upload_offer'),
]