from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/download/', views.start_download, name='start_download'),
    path('api/progress/<str:task_id>/', views.progress, name='progress'),
    path('api/file/<str:task_id>/', views.download_file, name='download_file'),
]