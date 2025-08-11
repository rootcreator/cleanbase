from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_customer = models.BooleanField(default=False)
    is_service_provider = models.BooleanField(default=False)
    
class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ServiceProvider(models.Model):
    user = models.OneToOneField('core.User', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    bio = models.TextField(blank=True)
    address = models.TextField()
    rating = models.FloatField(default=0.0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.user.username


class Customer(models.Model):
    user = models.OneToOneField('core.User', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    # other fields...

    def __str__(self):
        return self.user.username


class Service(models.Model):
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.IntegerField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} by {self.provider.user.username}"


    
    
class Booking(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    scheduled_time = models.DateTimeField()
    status_choices = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='pending')
    address = models.TextField()
    is_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.customer.user.username} -> {self.service.title} on {self.scheduled_time}"


    
class Availability(models.Model):
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ['provider', 'date', 'start_time']

    def __str__(self):
        return f"{self.provider.user.username}: {self.date} - {self.start_time} to {self.end_time}"
        
