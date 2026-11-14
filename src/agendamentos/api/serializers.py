from django.core.exceptions import ValidationError as ErroDjango
from rest_framework import serializers

from agendamentos.models import Agendamento
from agendamentos.models import ParticipacaoAgendamento
from agendamentos.models import Espaco
from agendamentos.models import Equipamento
from usuarios.models import Atleta
from usuarios.models import Profissional
from usuarios.models import Funcionario


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


# Serializa os dados de cada participação para a tela de detalhes.
class ParticipacaoDetalheSerializer(ParticipacaoAgendamentoSerializer):

    # Acrescenta o nome do atleta, mantendo seu ID original.
    atleta_nome = serializers.CharField(
        source="atleta.nome",
        read_only=True,
    )

    # Retorna a descrição legível do tipo de participação.
    tipo_descricao = serializers.CharField(
        source="get_tipo_display",
        read_only=True,
    )

    # Retorna a descrição legível da situação da participação.
    situacao_descricao = serializers.CharField(
        source="get_situacao_display",
        read_only=True,
    )

    # Retorna a descrição do funcionário que registrou a participação.
    registrado_por_descricao = serializers.StringRelatedField(
        source="registrado_por",
        read_only=True,
    )

    class Meta(ParticipacaoAgendamentoSerializer.Meta):
        # Herda os campos existentes e acrescenta os campos de detalhes.
        fields = ParticipacaoAgendamentoSerializer.Meta.fields + [
            "atleta_nome",
            "tipo_descricao",
            "situacao_descricao",
            "registrado_por_descricao",
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


# Serializa os dados necessários para a página Agenda.
class AgendamentoListaSerializer(serializers.ModelSerializer):

    # Retorna a descrição do profissional, além do ID original.
    profissional_descricao = serializers.StringRelatedField(
        source="profissional",
        read_only=True,
    )

    # Retorna a descrição do espaço, além do ID original.
    espaco_descricao = serializers.StringRelatedField(
        source="espaco",
        read_only=True,
    )

    # Retorna os textos exibidos na interface.
    modalidade_descricao = serializers.CharField(
        source="get_modalidade_display",
        read_only=True,
    )
    situacao_descricao = serializers.CharField(
        source="get_situacao_display",
        read_only=True,
    )

    # Campos calculados a partir das participações do agendamento.
    atletas = serializers.SerializerMethodField()
    atletas_nomes = serializers.SerializerMethodField()
    inscritos_ativos = serializers.SerializerMethodField()

    def _participacoes_ativas(self, agendamento):
        # Considera todas as participações, exceto as canceladas.
        return [
            participacao
            for participacao in agendamento.participacoes.all()
            if participacao.situacao != "cancelada"
        ]

    def get_atletas(self, agendamento):
        # Retorna os IDs dos atletas não cancelados.
        return [
            participacao.atleta_id
            for participacao in self._participacoes_ativas(agendamento)
        ]

    def get_atletas_nomes(self, agendamento):
        # Retorna os nomes exibidos na coluna Participantes.
        return [
            participacao.atleta.nome
            for participacao in self._participacoes_ativas(agendamento)
        ]

    def get_inscritos_ativos(self, agendamento):
        # Calcula a quantidade de participantes não cancelados.
        return len(self._participacoes_ativas(agendamento))

    class Meta:
        model = Agendamento
        fields = [
            "id",
            "inicio",
            "fim",
            "profissional",
            "profissional_descricao",
            "espaco",
            "espaco_descricao",
            "modalidade",
            "modalidade_descricao",
            "limite_participantes",
            "atletas",
            "atletas_nomes",
            "inscritos_ativos",
            "situacao",
            "situacao_descricao",
        ]
        read_only_fields = fields


# Serializa as informações completas da tela de detalhes.
class AgendamentoDetalheSerializer(AgendamentoSerializer):

    # Acrescenta as descrições dos relacionamentos.
    profissional_descricao = serializers.StringRelatedField(
        source="profissional",
        read_only=True,
    )

    espaco_descricao = serializers.StringRelatedField(
        source="espaco",
        read_only=True,
    )

    registrado_por_descricao = serializers.StringRelatedField(
        source="registrado_por",
        read_only=True,
    )

    # Acrescenta as descrições da modalidade e da situação.
    modalidade_descricao = serializers.CharField(
        source="get_modalidade_display",
        read_only=True,
    )

    situacao_descricao = serializers.CharField(
        source="get_situacao_display",
        read_only=True,
    )

    # Retorna os equipamentos com ID, nome e tipo.
    equipamentos_detalhes = EquipamentoSerializer(
        source="equipamentos",
        many=True,
        read_only=True,
    )

    # Retorna os dados individuais de todas as participações.
    participacoes = ParticipacaoDetalheSerializer(
        many=True,
        read_only=True,
    )

    # Calcula a quantidade de inscritos ativos.
    inscritos_ativos = serializers.SerializerMethodField()

    def get_inscritos_ativos(self, agendamento):
        # Conta as participações que não foram canceladas.
        return sum(
            1
            for participacao in agendamento.participacoes.all()
            if participacao.situacao != "cancelada"
        )

    class Meta(AgendamentoSerializer.Meta):
        # Mantém os campos originais e acrescenta os detalhes da tela.
        fields = AgendamentoSerializer.Meta.fields + [
            "profissional_descricao",
            "espaco_descricao",
            "registrado_por_descricao",
            "modalidade_descricao",
            "situacao_descricao",
            "equipamentos_detalhes",
            "participacoes",
            "inscritos_ativos",
        ]
        read_only_fields = fields

class ProfissionalSerializer(serializers.ModelSerializer):
    nome = serializers.SerializerMethodField()

    class Meta:
        model = Profissional
        fields = ["id", "nome", "especialidade", "ativo"]

    def get_nome(self, profissional):
        user = profissional.usuario.user
        return user.get_full_name() or user.username