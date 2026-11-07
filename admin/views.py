from django.db.models import F
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.template import loader
from django.urls import reverse
from accounts.models import *
import http.client
import json

def _admin(request):
    if not request.user.is_authenticated:
        return None, JsonResponse({"error": "You are not logged in."}, status=401)
    if request.user.user_type != admin:
        return None, JsonResponse({"error": "You must be an admin to perform this."}, status=403)
    try:
        return request.user.admin, None
    except Admin.DoesNotExist:
        return None, JsonResponse("error": "Admin profile not found.", status=404)