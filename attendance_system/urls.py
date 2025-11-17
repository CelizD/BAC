from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('detection.urls')),  # Incluye las URLs de la API
    path('', lambda request: redirect('/api/health/')),  # Redirige la raíz a health check
]