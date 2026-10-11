# project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),  # URLs tradicionais
    path('api/', include('app.urls')),  # URLs da API
]