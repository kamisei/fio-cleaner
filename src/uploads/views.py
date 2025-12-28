from django.shortcuts import render


def upload_csv(request):
    return render(request, "uploads/upload.html")
