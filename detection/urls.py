# detection/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('add_camera/', views.add_camera, name='add_camera'),
    path('start/', views.start_detection, name='start_detection'),
    path('stop/', views.stop_detection, name='stop_detection'),
    path('remove/', views.remove_camera, name='remove_camera'),
    path('attendance/', views.get_attendance, name='get_attendance'),
]