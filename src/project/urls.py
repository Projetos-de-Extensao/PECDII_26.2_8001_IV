# project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('agendamentos/', include('agendamentos.urls')),
    path('', include('app.urls')),  # URLs tradicionais
    path('api/', include('api.urls')),  # API REST do siste,a
]
