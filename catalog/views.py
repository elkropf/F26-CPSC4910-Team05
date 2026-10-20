from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404
from django.template import loader
from django.urls import reverse
from accounts.models import *
import http.client

def catalog_page(request):
    template = loader.get_template('catalog_page.html')

    conn = http.client.HTTPSConnection("api.ebay.com")
    payload = 'grant_type=client_credentials&scope=https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope'
    headers = {
        'Authorization': '',
        'Cookie': 'ak_bmsc=5D333C71CD70594DB40EC2E02C3AB134~000000000000000000000000000000~YAAQhkA2F3eeFzyhAQAA22guWwHwF8863CEcEw1sukIiwh2s8w0E4Z/5osWopnsx0ViGVI1t1ZNhBXaeDHn+xRP8dHYCi6DlaO2uLjLVermcHSBbePpheyiYIh2RMpyu6O0u0oo/IQGs9UtI8bX4ErnAPP8a7Pkd4uObpCD8t3JYBBN0a4qNF2P7hxeIXqSIeWRXIA+STJuT/Hs2iIZvKb2GHjPwaGmFyUiVFOipzdyPHFE7ZJQGuVle1SIw2w/D9Ixseut8HTMLAE6OrIOSA+Q3jSYAKyBRycmvC4W3zQXu5tVBzNA/e79TBxeBPxYRhNmEarYoZaP1d8/JBNGcgrHXg32B6YI4yB4=',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    conn.request("POST", "/identity/v1/oauth2/token", payload, headers)
    res = conn.getresponse()
    data = res.read()
    decoded = data.decode("utf-8")
    decoded = decoded.removeprefix('{"access_token":"')
    i = decoded.index('"')
    j = len(decoded)
    decoded = decoded.removesuffix(decoded[i:j])
    
    conn = http.client.HTTPSConnection("api.ebay.com")
    payload = ''
    headers = {
      'Cookie': 'ak_bmsc=5D333C71CD70594DB40EC2E02C3AB134~000000000000000000000000000000~YAAQhkA2F3eeFzyhAQAA22guWwHwF8863CEcEw1sukIiwh2s8w0E4Z/5osWopnsx0ViGVI1t1ZNhBXaeDHn+xRP8dHYCi6DlaO2uLjLVermcHSBbePpheyiYIh2RMpyu6O0u0oo/IQGs9UtI8bX4ErnAPP8a7Pkd4uObpCD8t3JYBBN0a4qNF2P7hxeIXqSIeWRXIA+STJuT/Hs2iIZvKb2GHjPwaGmFyUiVFOipzdyPHFE7ZJQGuVle1SIw2w/D9Ixseut8HTMLAE6OrIOSA+Q3jSYAKyBRycmvC4W3zQXu5tVBzNA/e79TBxeBPxYRhNmEarYoZaP1d8/JBNGcgrHXg32B6YI4yB4=',
      'Authorization': ' '.join(['Bearer', decoded])
    }
    conn.request("GET", "/buy/browse/v1/item_summary/search?q=pen&limit=10&offset=0", payload, headers)
    res = conn.getresponse()
    data = res.read()

    context = {
        'response': data.decode("utf-8"),
    }
    return HttpResponse(template.render(context, request))