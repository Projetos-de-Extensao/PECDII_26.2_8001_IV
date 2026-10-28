from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EspacoViewSet
from .views import EquipamentoViewSet

router = DefaultRouter()
router.register("espacos", EspacoViewSet, basename="espaco")
router.register("equipamentos", EquipamentoViewSet, basename="equipamento")

urlpatterns = [
    path("", include(router.urls)),
]