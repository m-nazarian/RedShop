from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.utils.html import format_html
from mptt.admin import DraggableMPTTAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from .models import *


# -----------------------------
# 🔹 Inline ها
# -----------------------------

class ImageInline(TabularInline):
    model = Image
    extra = 0
    tab = True


class ProductFeatureValueInline(TabularInline):
    model = ProductFeatureValue
    extra = 0
    tab = True


class CommentLikeInline(TabularInline):
    model = CommentLike
    extra = 0
    readonly_fields = ('created',)
    can_delete = False
    tab = True


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
class BrandAdmin(ModelAdmin):
    list_display = ('name', 'established')
    search_fields = ('name',)


@admin.register(Color)
class ColorAdmin(ModelAdmin):
    list_display = ('name', 'color_preview', 'hex_code')
    search_fields = ('name',)

    @display(description="پیش‌نمایش", label=True)
    def color_preview(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: #{}; border-radius: 50%; border: 1px solid #ccc;"></div>',
            obj.hex_code
        )


# -----------------------------
# 🔹 ویژگی‌های پویا
# -----------------------------

@admin.register(CategoryFeature)
class CategoryFeatureAdmin(ModelAdmin):
    list_display = ('name', 'category', 'group', 'created_jalali')
    list_filter = ('category', 'group')
    search_fields = ('name', 'category__name')
    list_filter_submit = True

    def created_jalali(self, obj):
        return obj.created.strftime("%Y/%m/%d")

    created_jalali.short_description = "تاریخ ایجاد"


@admin.register(ProductFeatureValue)
class ProductFeatureValueAdmin(ModelAdmin):
    list_display = ('product', 'feature', 'value')
    search_fields = ('product__name', 'feature__name', 'value')
    list_filter_submit = True


@admin.register(FeatureGroup)
class FeatureGroupAdmin(ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)


# -----------------------------
# 🔹 محصول‌ها
# -----------------------------

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('product_image', 'name', 'category', 'brand', 'price', 'inventory', 'created_jalali')
    list_filter = ('category', 'brand', 'created')
    search_fields = ('name', 'description')
    autocomplete_fields = ['category', 'brand']
    list_editable = ('inventory',)
    list_per_page = 20
    list_filter_submit = True

    inlines = [ImageInline, ProductFeatureValueInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'brand').prefetch_related('images')

    # نمایش قیمت با فرمت پول
    @display(description="قیمت", label=True)
    def price_display(self, obj):
        return f"{obj.new_price:,} تومان"

    # وضعیت موجودی با رنگ‌بندی Unfold
    @display(description="وضعیت", label={
        "موجود": "success",  # سبز
        "کم": "warning",  # زرد
        "ناموجود": "danger"  # قرمز
    })
    def inventory_status(self, obj):
        if obj.inventory > 5:
            return "موجود"
        elif obj.inventory > 0:
            return "کم"
        else:
            return "ناموجود"

    # نمایش تصویر با استایل Tailwind
    def product_image(self, obj):
        img = obj.images.first()
        if img:
            return format_html('<img src="{}" class="rounded h-10 w-10 object-cover border border-gray-200">',
                               img.file.url)
        return "-"

    product_image.short_description = 'تصویر'
    product_image.allow_tags = True

    def created_jalali(self, obj):
        return obj.created.strftime("%Y/%m/%d")

    created_jalali.short_description = "تاریخ ایجاد"

    class Media:
        css = {'all': ('admin/css/select2_dark.css',)}
        js = ('admin/js/product_feature_autocomplete_filter.js', 'admin/js/slugify_fa.js')


# کلاس کمکی برای Autocomplete
class CategoryFeatureAutocomplete(AutocompleteJsonView):
    def get_queryset(self):
        qs = super().get_queryset()
        category_id = self.request.GET.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs


# -----------------------------
# 🔹 نظرات
# -----------------------------

@admin.register(ProductComment)
class ProductCommentAdmin(ModelAdmin):
    list_display = (
    'user', 'product', 'score_badge', 'suggest_badge', 'show_likes', 'show_dislikes', 'active', 'created_jalali')
    list_filter = ('active', 'score', 'suggest', 'created')
    search_fields = ('user__phone', 'product__name', 'text')
    list_editable = ('active',)
    actions = ['approve_comments']
    list_filter_submit = True

    inlines = [CommentLikeInline]

    @display(description="امتیاز", label=True)
    def score_badge(self, obj):
        return str(obj.score)

    @display(description="پیشنهاد", label={
        'yes': 'success',
        'no': 'danger',
        'none': 'secondary'
    })
    def suggest_badge(self, obj):
        return obj.suggest

    def show_likes(self, obj): return obj.likes_count

    show_likes.short_description = '👍'

    def show_dislikes(self, obj): return obj.dislikes_count

    show_dislikes.short_description = '👎'

    def created_jalali(self, obj):
        return obj.created.strftime("%Y/%m/%d")

    created_jalali.short_description = "تاریخ"

    def approve_comments(self, request, queryset):
        queryset.update(active=True)

    approve_comments.short_description = "تایید نظرات انتخاب شده"