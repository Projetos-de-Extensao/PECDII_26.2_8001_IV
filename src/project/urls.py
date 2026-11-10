# project/urls.py
from django.views.generic import RedirectView
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('agendamentos/', include('agendamentos.urls')),
    path('api/', include('agendamentos.api.urls')),  # API REST do sistema
    path('', RedirectView.as_view(url='/agendamentos/')),
]
