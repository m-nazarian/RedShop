from django.urls import path
from . import views

app_name = 'shop'


urlpatterns = [
    path('', views.index, name="index"),
    path('products/', views.product_list, name='product_list'),
    path('products/filter/', views.filter_products, name='filter_products'),
    path('products/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('api/features/<int:category_id>/', views.get_category_features, name='get_category_features'),
    path('categoryfeature/autocomplete/', views.categoryfeature_autocomplete, name='categoryfeature_autocomplete'),
    path('api/search/', views.search_suggestions, name='search_suggestions'),
    path('comment/add/<int:product_id>/', views.add_product_comment, name='add_product_comment'),
    path('comment/react/<int:comment_id>/', views.like_comment, name='like_comment'),

]