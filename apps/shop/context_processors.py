from .models import Category


def common_data(request):
    """
    این داده‌ها در تمام صفحات سایت در دسترس هستند.
    """
    return {
        # برای منوی درختی در هدر (recurse tree به همه نودها نیاز دارد)
        'categories_tree': Category.objects.all(),

        # برای نمایش باکس‌ها در صفحه اصلی (فقط والدین)
        'categories_parents': Category.objects.filter(parent=None)
    }