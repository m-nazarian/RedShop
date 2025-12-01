from django.urls import path
from . import views

app_name = 'compare'

urlpatterns = [
    path('', views.show_compare, name='show_compare'),
    path('add/<int:product_id>/', views.add_to_compare, name='add_to_compare'),
    path('remove/<int:product_id>/', views.remove_from_compare, name='remove_from_compare'),
    path('suggestions/', views.compare_suggestions, name='suggestions'),
]