from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    CustomerViewSet, ServiceProviderViewSet,
    ServiceCategoryViewSet, ServiceViewSet,
    BookingViewSet, AvailabilityViewSet,
    RegisterCustomerView, RegisterProviderView,
    available_slots, recommend_providers,
    initiate_payment, paystack_webhook
)

from .view_templates import (
    register_customer_view, register_provider_view, book_service_view,home_view, ServiceListView, ServiceDetailView,booking_create
)

# DRF router
router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'providers', ServiceProviderViewSet)
router.register(r'categories', ServiceCategoryViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'bookings', BookingViewSet)
router.register(r'availability', AvailabilityViewSet)

# Final urlpatterns (merged)
urlpatterns = [
    # Template views
    path('register/customer/', register_customer_view, name='register_customer'),
    path('register/provider/', register_provider_view, name='register_provider'),
    path('book/', book_service_view, name='book_service'),
    path('', home_view, name='home'),
    path('services/', ServiceListView.as_view(), name='service_list'),
    path('services/<int:pk>/', ServiceDetailView.as_view(), name='service_detail'),
    path('book/<int:service_id>/', booking_create, name='booking_create'),

    # API routes
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/customer/', RegisterCustomerView.as_view(), name='register_customer_api'),
    path('api/register/provider/', RegisterProviderView.as_view(), name='register_provider_api'),
    path('api/available-slots/<int:provider_id>/', available_slots),
    path('recommend/providers/', recommend_providers),
    path("pay/booking/<int:booking_id>/", initiate_payment),
    path("paystack/callback/", paystack_webhook),
]