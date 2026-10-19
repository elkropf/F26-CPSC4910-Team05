from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404
from django.template import loader
from django.urls import reverse
from accounts.models import *
import http.client

def catalog_page(request):
    template = loader.get_template('catalog_page.html')

    conn = http.client.HTTPSConnection("api.ebay.com")
    payload = ''
    headers = {
        'Authorization': ''
    }
    conn.request("POST", "/identity/v1/oauth2/token", payload, headers)
    res = conn.getresponse()
    data = res.read()

    context = {
        'response': data.decode("utf-8")
    }
    return HttpResponse(template.render(context, request))
