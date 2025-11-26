from django.db import models


class MediaDownload(models.Model):
    MEDIA_TYPES = [
        ('video', 'Vidéo'),
        ('audio', 'Audio'),
        ('miniature', 'Miniature'),
    ]

    QUALITY_CHOICES = [
        ('best', 'Meilleure'),
        ('1080', 'Haute'),
        ('720', 'Moyenne'),
        ('480', 'Basique'),
    ]

    url = models.URLField()
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default='video')
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default='best')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.media_type} - {self.quality}"

    class Meta:
        verbose_name = "Téléchargement"
        verbose_name_plural = "Téléchargements"