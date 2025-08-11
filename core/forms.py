from django import forms
from .models import Customer, ServiceProvider, Booking, Availability


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['user', 'phone', 'name', 'email']


class ServiceProviderForm(forms.ModelForm):
    class Meta:
        model = ServiceProvider
        fields = [
            'user', 'phone', 'bio', 'address', 'rating',
            'latitude', 'longitude'
        ]


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'customer', 'service', 'scheduled_time', 'status',
            'address', 'is_paid', 'payment_reference'
        ]


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ['provider', 'date', 'start_time', 'end_time']