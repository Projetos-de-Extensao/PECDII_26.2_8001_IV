from rest_framework import serializers

from app.models import Espaco
from app.models import Equipamento


class EspacoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Espaco
        fields = ["id", "nome", "tipo", "capacidade"]

class EquipamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipamento
        fields = ["id", "nome", "tipo"]