from django.shortcuts import render
from .models import AboutSprintInfo, AboutProductInfo
from django.http import JsonResponse

# Create your views here.
def about_information(request):
    # Create About Information databases.
    product_info = AboutProductInfo.objects.first()
    sprint_info = AboutSprintInfo.objects.order_by('-sprint_number').first()

    # Error handling if no data inputted
    if not product_info:
        return JsonResponse({'error': 'No product information found.'})
    if not sprint_info:
        return JsonResponse({'error': 'No sprint information found.'})

    # using jsonResponse due to front end using REACT
    return JsonResponse({
            'team_number': product_info.team_number,
            'product_name': product_info.product_name,
            'product_description': product_info.product_description,
            'sprint_number': sprint_info.sprint_number,
            'release_date': sprint_info.release_date,
            'created_at': sprint_info.created_at,
    })

