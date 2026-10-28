from rest_framework import viewsets

from app.models import Espaco
from app.models import Equipamento

from .serializers import EspacoSerializer
from .serializers import EquipamentoSerializer


class EspacoViewSet(viewsets.ModelViewSet):
    queryset = Espaco.objects.all().order_by("nome")
    serializer_class = EspacoSerializer

class EquipamentoViewSet(viewsets.ModelViewSet):
    queryset = Equipamento.objects.all().order_by("nome")
    serializer_class = EquipamentoSerializer