from rest_framework import serializers

from app.models import Espaco
from app.models import Equipamento
from usuarios.models import Atleta

from django.core.exceptions import ValidationError as ErroDjango

class EspacoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Espaco
        fields = ["id", "nome", "tipo", "capacidade"]

class EquipamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipamento
        fields = ["id", "nome", "tipo"]
    
class AtletaSerializer(serializers.ModelSerializer):
    idade = serializers.IntegerField(read_only=True)

    class Meta:
        model = Atleta
        fields = [
            "id",
            "nome",
            "email",
            "telefone",
            "data_de_nascimento",
            "idade",
            "objetivos",
            "ativo",
            "responsavel",
        ]
    def validate(self, dados):
        # Reaproveita o clean() do model Atleta (telefone e data de nascimento)
        atleta = Atleta(
            telefone=dados.get(
                "telefone", getattr(self.instance, "telefone", "")
            ),
            data_de_nascimento=dados.get(
                "data_de_nascimento",
                getattr(self.instance, "data_de_nascimento", None),
            ),
        )
        try:
            atleta.clean()
        except ErroDjango as erro:
            raise serializers.ValidationError(erro.message_dict)
        return dados