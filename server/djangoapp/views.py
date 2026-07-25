from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from datetime import datetime

from django.http import JsonResponse
from django.contrib.auth import login, authenticate
import logging
import json
from django.views.decorators.csrf import csrf_exempt
from .models import CarMake, CarModel
from .populate import initiate
from .restapis import get_request, analyze_review_sentiments, post_review


# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.

# Create a `login_request` view to handle sign in request
@csrf_exempt
def login_user(request):
    if request.method == 'GET':
        return render(request, 'index.html')

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    username = data.get('userName')
    password = data.get('password')

    if not username or not password:
        return JsonResponse({'error': 'Missing credentials'}, status=400)

    user = authenticate(username=username, password=password)
    response_data = {"userName": username}
    if user is not None:
        login(request, user)
        response_data = {"userName": username, "status": "Authenticated"}

    return JsonResponse(response_data)


@csrf_exempt
def logout_user(request):
    auth_logout(request)
    return JsonResponse({"userName": ""})


@csrf_exempt
def registration(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    username = data.get('userName')
    password = data.get('password')
    first_name = data.get('firstName', '')
    last_name = data.get('lastName', '')
    email = data.get('email', '')

    if not username or not password:
        return JsonResponse({'error': 'Missing credentials'}, status=400)

    try:
        User.objects.get(username=username)
        return JsonResponse({'userName': username, 'error': 'Already Registered'})
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )
        login(request, user)
        return JsonResponse({'userName': username, 'status': 'Authenticated'})


def get_cars(request):
    count = CarMake.objects.filter().count()
    if count == 0:
        initiate()

    car_models = CarModel.objects.select_related('car_make')
    cars = []
    for car_model in car_models:
        cars.append({"CarModel": car_model.name, "CarMake": car_model.car_make.name})
    return JsonResponse({"CarModels": cars})


def get_dealerships(request, state='All'):
    endpoint = '/fetchDealers' if state == 'All' else f'/fetchDealers/{state}'
    dealerships = get_request(endpoint)
    return JsonResponse({"status": 200, "dealers": dealerships})


def get_dealer_details(request, dealer_id):
    if dealer_id:
        endpoint = f'/fetchDealer/{dealer_id}'
        dealership = get_request(endpoint)
        return JsonResponse({"status": 200, "dealer": dealership})
    return JsonResponse({"status": 400, "message": "Bad Request"})


def get_dealer_reviews(request, dealer_id):
    if dealer_id:
        endpoint = f'/fetchReviews/dealer/{dealer_id}'
        reviews = get_request(endpoint)
        for review_detail in reviews:
            response = analyze_review_sentiments(review_detail['review'])
            review_detail['sentiment'] = response.get('sentiment', 'neutral')
        return JsonResponse({"status": 200, "reviews": reviews})
    return JsonResponse({"status": 400, "message": "Bad Request"})


@csrf_exempt
def add_review(request):
    if request.user.is_anonymous:
        return JsonResponse({"status": 403, "message": "Unauthorized"})

    data = json.loads(request.body)
    try:
        response = post_review(data)
        return JsonResponse({"status": 200, "message": "Review posted", "response": response})
    except Exception:
        return JsonResponse({"status": 401, "message": "Error in posting review"})

# # Update the `get_dealerships` view to render the index page with
# a list of dealerships
# def get_dealerships(request):
# ...

# Create a `get_dealer_reviews` view to render the reviews of a dealer
# def get_dealer_reviews(request,dealer_id):
# ...

# Create a `get_dealer_details` view to render the dealer details
# def get_dealer_details(request, dealer_id):
# ...

# Create a `add_review` view to submit a review
# def add_review(request):
# ...
