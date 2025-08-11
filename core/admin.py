from django.contrib import admin
from .models import (
    User, Customer, ServiceProvider, ServiceCategory,
    Service, Booking
)

admin.site.register(User)
admin.site.register(Customer)
admin.site.register(ServiceProvider)
admin.site.register(ServiceCategory)
admin.site.register(Service)
admin.site.register(Booking)