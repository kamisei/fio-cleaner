from django.urls import path
from . import views

urlpatterns = [
    path("", views.upload_csv, name="upload_csv"),
    path("normalize-preview/", views.normalize_preview, name="normalize_preview"),
]
