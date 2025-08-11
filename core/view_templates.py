from datetime import datetime
from statistics import mean
from geopy.distance import geodesic
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.http import JsonResponse
import requests
from django.shortcuts import render, redirect
from .forms import CustomerForm, ServiceProviderForm, BookingForm

from .models import (
    Customer, ServiceProvider, ServiceCategory, Service,
    Booking, Availability
)
from .forms import BookingForm, AvailabilityForm


# ---------------------------
# Template Views
# ---------------------------

class ServiceListView(ListView):
    model = Service
    template_name = "services/service_list.html"
    context_object_name = "services"


class ServiceDetailView(DetailView):
    model = Service
    template_name = "services/service_detail.html"
    context_object_name = "service"


@login_required
def availability_list(request):
    provider = ServiceProvider.objects.filter(user=request.user).first()
    availabilities = Availability.objects.filter(provider=provider)
    return render(request, "availability/list.html", {"availabilities": availabilities})


@login_required
def availability_create(request):
    provider = ServiceProvider.objects.get(user=request.user)
    if request.method == "POST":
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.provider = provider
            availability.save()
            return redirect("availability_list")
    else:
        form = AvailabilityForm()
    return render(request, "availability/create.html", {"form": form})


@login_required
def booking_list(request):
    customer = Customer.objects.filter(user=request.user).first()
    bookings = Booking.objects.filter(customer=customer)
    return render(request, "bookings/list.html", {"bookings": bookings})


@login_required
def booking_create(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = Customer.objects.get(user=request.user)
            booking.service = service
            booking.save()
            return redirect("booking_list")
    else:
        form = BookingForm()
    return render(request, "bookings/create.html", {"form": form, "service": service})


@login_required
def recommend_providers_template(request):
    category_id = request.GET.get("category_id")
    date_str = request.GET.get("date")  # YYYY-MM-DD
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")

    if not (lat and lng and date_str and category_id):
        return render(request, "recommendations/error.html", {
            "error": "lat, lng, date, and category_id are required"
        })

    user_location = (float(lat), float(lng))
    date = datetime.strptime(date_str, "%Y-%m-%d").date()

    services = Service.objects.filter(category_id=category_id, is_available=True)
    if not services.exists():
        return render(request, "recommendations/error.html", {"error": "No services found for this category"})

    avg_price = mean([float(s.price) for s in services])
    recommendations = []

    for service in services:
        provider = service.provider
        if not provider.latitude or not provider.longitude:
            continue

        distance_km = geodesic(user_location, (provider.latitude, provider.longitude)).km
        has_slot = Availability.objects.filter(provider=provider, date=date).exists()
        if not has_slot:
            continue

        price_factor = float(service.price) / avg_price if avg_price else 1.0
        score = (
            -provider.rating * 2 +
            distance_km * 1.5 +
            price_factor * 2
        )

        recommendations.append({
            "provider": provider,
            "service": service,
            "price": float(service.price),
            "distance_km": round(distance_km, 2),
            "score": round(score, 2)
        })

    recommendations.sort(key=lambda x: x["score"])
    return render(request, "recommendations/list.html", {"recommendations": recommendations})
    
    
def register_customer_view(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')  # replace with your homepage URL name
    else:
        form = CustomerForm()
    return render(request, 'core/register_customer.html', {'form': form})

def register_provider_view(request):
    if request.method == 'POST':
        form = ServiceProviderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ServiceProviderForm()
    return render(request, 'core/register_provider.html', {'form': form})

def book_service_view(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = BookingForm()
    return render(request, 'core/book_service.html', {'form': form})
    
def home_view(request):
    return render(request, "core/home.html")
    