from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, re_path


def regex_view(request):
    return HttpResponse("ok")


urlpatterns = [
    re_path(r"^django-admin/", admin.site.urls),
    re_path(r"^regex-search/$", regex_view, name="regex_search"),
    path("plain-search/", regex_view, name="plain_search"),
]
