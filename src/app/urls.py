# app/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.views import ProdutoViewSet

router = DefaultRouter()
router.register(r'produtos', ProdutoViewSet, basename='produto')

urlpatterns = [
    path('', include(router.urls)),
]