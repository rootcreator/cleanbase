from rest_framework import serializers
from .models import (
    User, Customer, ServiceProvider, ServiceCategory,
    Service, Booking, Availability
)
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Customer, ServiceProvider

User = get_user_model()

class RegisterCustomerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            is_customer=True
        )
        Customer.objects.create(user=user, phone="")
        return user


class RegisterProviderSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            is_service_provider=True
        )
        ServiceProvider.objects.create(user=user, phone="", address="")
        return user
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_customer', 'is_service_provider']


class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Customer
        fields = '__all__'


class ServiceProviderSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = ServiceProvider
        fields = '__all__'


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'


class ServiceSerializer(serializers.ModelSerializer):
    provider = ServiceProviderSerializer()
    category = ServiceCategorySerializer()

    class Meta:
        model = Service
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    service = ServiceSerializer()

    class Meta:
        model = Booking
        fields = '__all__'
        
class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = '__all__'
        
