from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.utils.html import format_html # برای نمایش عکس
from mptt.admin import DraggableMPTTAdmin
from .models import *

# -----------------------------
# 🔹 Inline ها
# -----------------------------

class ImageInline(admin.TabularInline):
    model = Image
    extra = 0


class ProductFeatureValueInline(admin.TabularInline):
    model = ProductFeatureValue
    extra = 1



# -----------------------------
# 🔹 مدل‌های پایه
# -----------------------------

@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("tree_actions", "indented_title", "parent")
    list_display_links = ("indented_title",)
    search_fields = ['name']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'established')
    search_fields = ('name',)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code')
    search_fields = ('name',)


# -----------------------------
# 🔹 ویژگی‌های پویا
# -----------------------------

@admin.register(CategoryFeature)
class CategoryFeatureAdmin(admin.ModelAdmin):
    list_display = ('category', 'group', 'name', 'created')
    list_filter = ('category', 'group')
    search_fields = ('name', 'category__name')


@admin.register(ProductFeatureValue)
class ProductFeatureValueAdmin(admin.ModelAdmin):
    list_display = ('product', 'feature', 'value')
    search_fields = ('product__name', 'feature__name', 'value')


@admin.register(FeatureGroup)
class FeatureGroupAdmin(admin.ModelAdmin):
    list_display = ('category', 'name')
    list_filter = ('category',)
    search_fields = ('name',)

# -----------------------------
# 🔹 محصول‌ها
# -----------------------------

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_image', 'name', 'category', 'brand', 'price', 'inventory', 'created')

    # استفاده از autocomplete_fields برای فیلترهای سنگین (دسته و برند)
    autocomplete_fields = ['category', 'brand']

    search_fields = ('name', 'description')
    list_editable = ('inventory', 'price')
    list_per_page = 20

    inlines = [ImageInline, ProductFeatureValueInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'brand').prefetch_related('images')

    def product_image(self, obj):
        img = obj.images.first()
        if img:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:5px;" />', img.file.url)
        return "-"

    product_image.short_description = 'تصویر'

    class Media:
        css = {
            'all': ('admin/css/select2_dark.css',)
        }
        js = (
            'admin/js/product_feature_autocomplete_filter.js',
            'admin/js/slugify_fa.js',
        )


class CategoryFeatureAutocomplete(AutocompleteJsonView):
    def get_queryset(self):
        qs = super().get_queryset()
        category_id = self.request.GET.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs