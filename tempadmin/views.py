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
    if request.user.user_type != UserType.ADMIN:
        return None, JsonResponse({"error": "You must be an admin to perform this."}, status=403)
    try:
        return request.user.admin, None
    except Admin.DoesNotExist:
        return None, JsonResponse({"error": "Admin profile not found."}, status=404)

def driver_list_page(request):
    admin, response = _admin(request)
    if response != None:
        return response

    drivers = Driver.objects.all()
    template = loader.get_template('driver_list.html')
    context = {
        'drivers': drivers,
    }
    return HttpResponse(template.render(context, request))

def setup_driver_view(request, driver):
    admin, response = _admin(request)
    if response != None:
        return response
    
    request.session['view_user'] = driver
    return HttpResponseRedirect(reverse('accounts:driver_homepage'))

def sponsor_list_page(request):
    admin, response = _admin(request)
    if response != None:
        return response

    sponsors = Sponsor.objects.all()
    template = loader.get_template('sponsor_list.html')
    context = {
        'sponsors': sponsors,
    }
    return HttpResponse(template.render(context, request))

def setup_sponsor_view(request, sponsor):
    admin, response = _admin(request)
    if response != None:
        return response
    
    request.session['view_user'] = sponsor
    return HttpResponseRedirect(reverse('accounts:sponsor_homepage'))