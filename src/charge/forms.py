from django import forms
from .models import MediaDownload

class MediaDownloadForm(forms.ModelForm):
    class Meta:
        model = MediaDownload
        fields = ['url', 'media_type', 'quality']
        widgets = {
            'url': forms.URLInput(attrs={'id':'url', 'name':'url', 'class': 'w-full px-4 py-3 pr-12 border-2 border-gray-300 rounded-xl input-focus transition-all duration-300 text-gray-700 placeholder-gray-400', 'placeholder': 'https://exemple.com/…'}),
            'media_type': forms.Select(attrs={'id':'type', 'name':'media_type', 'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-xl bg-white text-gray-700'}),
            'quality': forms.Select(attrs={'id':'quality', 'name':'quality', 'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-xl bg-white text-gray-700'}),
        }