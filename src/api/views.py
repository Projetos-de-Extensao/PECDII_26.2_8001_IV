from rest_framework import viewsets

from app.models import Espaco
from app.models import Equipamento
from usuarios.models import Atleta

from .serializers import EspacoSerializer
from .serializers import EquipamentoSerializer
from .serializers import AtletaSerializer


class EspacoViewSet(viewsets.ModelViewSet):
    queryset = Espaco.objects.all().order_by("nome")
    serializer_class = EspacoSerializer

class EquipamentoViewSet(viewsets.ModelViewSet):
    queryset = Equipamento.objects.all().order_by("nome")
    serializer_class = EquipamentoSerializer

class AtletaViewSet(viewsets.ModelViewSet):
    queryset = Atleta.objects.all().order_by("nome")
    serializer_class = AtletaSerializer