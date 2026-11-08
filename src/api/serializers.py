from django.core.exceptions import ValidationError as ErroDjango
from rest_framework import serializers

from agendamentos.models import Agendamento
from agendamentos.models import ParticipacaoAgendamento
from app.models import Espaco
from app.models import Equipamento
from usuarios.models import Atleta
from usuarios.models import Funcionario
from usuarios.models import Profissional


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

class AgendamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agendamento
        fields = [
            "id",
            "profissional",
            "espaco",
            "modalidade",
            "limite_participantes",
            "atletas",
            "equipamentos",
            "registrado_por",
            "inicio",
            "fim",
            "situacao",
            "observacoes",
            "motivo_cancelamento",
            "cancelado_em",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = fields
        
# Serializa a participação de um atleta em um agendamento
class ParticipacaoAgendamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParticipacaoAgendamento
        fields = [
            "id",
            "agendamento",
            "atleta",
            "registrado_por",
            "tipo",
            "situacao",
            "observacoes",
            "motivo_cancelamento",
            "cancelado_em",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = fields

class CriarAgendamentoSerializer(serializers.Serializer):
    profissional = serializers.PrimaryKeyRelatedField(
        queryset=Profissional.objects.all()
    )
    espaco = serializers.PrimaryKeyRelatedField(
        queryset=Espaco.objects.all()
    )
    atletas = serializers.PrimaryKeyRelatedField(
        queryset=Atleta.objects.all(),
        many=True,
        allow_empty=False,
    )
    equipamentos = serializers.PrimaryKeyRelatedField(
        queryset=Equipamento.objects.all(),
        many=True,
        required=False,
    )
    registrado_por = serializers.PrimaryKeyRelatedField(
        queryset=Funcionario.objects.all()
    )
    inicio = serializers.DateTimeField()
    fim = serializers.DateTimeField()
    modalidade = serializers.ChoiceField(
        choices=Agendamento.Modalidade.choices,
        required=False,
    )
    limite_participantes = serializers.IntegerField(
        min_value=1,
        required=False,
    )
    observacoes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    atletas_experimentais = serializers.PrimaryKeyRelatedField(
        queryset=Atleta.objects.all(),
        many=True,
        required=False,
    )

class InscricaoAgendamentoSerializer(serializers.Serializer):
    atleta = serializers.PrimaryKeyRelatedField(
        queryset=Atleta.objects.all()
    )
    experimental = serializers.BooleanField(
        required=False,
        default=False,
    )
    registrado_por = serializers.PrimaryKeyRelatedField(
        queryset=Funcionario.objects.all(),
        required=False,
        allow_null=True,
    )

class CancelamentoSerializer(serializers.Serializer):
    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
