from datetime import datetime
from statistics import mean

import requests
from geopy.distance import geodesic
from django.conf import settings
from rest_framework import viewsets, generics, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    User, Customer, ServiceProvider, ServiceCategory,
    Service, Booking, Availability
)
from .serializers import (
    CustomerSerializer, ServiceProviderSerializer, ServiceCategorySerializer,
    ServiceSerializer, BookingSerializer, RegisterCustomerSerializer,
    RegisterProviderSerializer, AvailabilitySerializer
)
from .permissions import IsServiceProvider, IsCustomer


# ---------------------------
# Availability
# ---------------------------
class AvailabilityViewSet(viewsets.ModelViewSet):
    queryset = Availability.objects.all()
    serializer_class = AvailabilitySerializer
    permission_classes = [IsServiceProvider]

    def perform_create(self, serializer):
        provider = ServiceProvider.objects.get(user=self.request.user)
        serializer.save(provider=provider)

    def get_queryset(self):
        provider = ServiceProvider.objects.filter(user=self.request.user).first()
        return Availability.objects.filter(provider=provider)


# ---------------------------
# Registration
# ---------------------------
class RegisterCustomerView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterCustomerSerializer


class RegisterProviderView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterProviderSerializer


# ---------------------------
# Basic CRUD ViewSets
# ---------------------------
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class ServiceProviderViewSet(viewsets.ModelViewSet):
    queryset = ServiceProvider.objects.all()
    serializer_class = ServiceProviderSerializer


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


# ---------------------------
# Booking
# ---------------------------
class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsCustomer]

    def perform_create(self, serializer):
        customer = Customer.objects.get(user=self.request.user)
        scheduled_time = serializer.validated_data['scheduled_time']
        service = serializer.validated_data['service']

        exists = Booking.objects.filter(
            service__provider=service.provider,
            scheduled_time=scheduled_time
        ).exists()

        if exists:
            raise serializers.ValidationError("This time slot is already booked.")

        serializer.save(customer=customer)

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all()
        customer = Customer.objects.filter(user=self.request.user).first()
        return Booking.objects.filter(customer=customer)


# ---------------------------
# Custom APIs
# ---------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_slots(request, provider_id):
    date_str = request.GET.get('date')  # expected format: YYYY-MM-DD
    if not date_str:
        return Response({"error": "date query param is required"}, status=400)

    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    availabilities = Availability.objects.filter(provider__id=provider_id, date=date)

    booked_times = Booking.objects.filter(
        service__provider__id=provider_id,
        scheduled_time__date=date
    ).values_list('scheduled_time__time', flat=True)

    filtered = [a for a in availabilities if a.start_time not in booked_times]

    serializer = AvailabilitySerializer(filtered, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, customer__user=request.user)
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found."}, status=404)

    if booking.is_paid:
        return Response({"message": "Already paid."})

    amount = int(booking.service.price * 100)  # kobo

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "email": request.user.email,
        "amount": amount,
        "reference": f"CLN-{booking.id}-{request.user.id}",
        "callback_url": "https://yourdomain.com/api/paystack/callback/"
    }

    response = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
    res_data = response.json()

    if response.status_code == 200 and res_data['status']:
        booking.payment_reference = res_data['data']['reference']
        booking.save()
        return Response({"checkout_url": res_data['data']['authorization_url']})
    else:
        return Response({"error": res_data.get('message', 'Failed to initialize payment')}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])  # Paystack sends requests without auth
def paystack_webhook(request):
    payload = request.data
    event = payload.get("event")

    if event == "charge.success":
        ref = payload['data']['reference']
        try:
            booking = Booking.objects.get(payment_reference=ref)
            booking.is_paid = True
            booking.save()
        except Booking.DoesNotExist:
            pass

    return Response(status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommend_providers(request):
    category_id = request.GET.get("category_id")
    date_str = request.GET.get("date")  # YYYY-MM-DD
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")

    if not (lat and lng and date_str and category_id):
        return Response({"error": "lat, lng, date, and category_id are required"}, status=400)

    user_location = (float(lat), float(lng))
    date = datetime.strptime(date_str, "%Y-%m-%d").date()

    services = Service.objects.filter(category_id=category_id, is_available=True)
    if not services.exists():
        return Response({"error": "No services found for this category"}, status=404)

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
            "provider": ServiceProviderSerializer(provider).data,
            "service_id": service.id,
            "service_title": service.title,
            "price": float(service.price),
            "distance_km": round(distance_km, 2),
            "score": round(score, 2)
        })

    recommendations.sort(key=lambda x: x["score"])
    return Response(recommendations)