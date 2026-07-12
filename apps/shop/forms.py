from django import forms
from .models import ProductComment

class ProductCommentForm(forms.ModelForm):
    class Meta:
        model = ProductComment
        fields = ['score', 'text', 'suggest']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-xl p-4 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors resize-none h-32',
                'placeholder': 'متن دیدگاه خود را اینجا بنویسید...'
            }),
            'suggest': forms.Select(attrs={  # گزینه‌ها خودکار از مدل خوانده می‌شوند
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 bg-white'
            }),
        }
        labels = {
            'score': 'امتیاز شما',
            'suggest': 'آیا خرید این محصول را به دیگران پیشنهاد می‌کنید؟'
        }