from django.contrib import admin
from .models import MediaDownload


@admin.register(MediaDownload)
class MediaDownloadAdmin(admin.ModelAdmin):
    list_display = ('url', 'media_type', 'quality', 'created_at')

