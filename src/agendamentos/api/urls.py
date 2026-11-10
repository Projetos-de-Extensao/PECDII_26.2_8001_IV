from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EspacoViewSet
from .views import EquipamentoViewSet
from .views import AtletaViewSet
from .views import AgendamentoViewSet

router = DefaultRouter()
router.register("espacos", EspacoViewSet, basename="espaco")
router.register("equipamentos", EquipamentoViewSet, basename="equipamento")
router.register("atletas", AtletaViewSet, basename="atleta")
router.register("agendamentos", AgendamentoViewSet, basename="agendamento")

urlpatterns = [
    path("", include(router.urls)),
]