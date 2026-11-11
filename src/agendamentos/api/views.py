from django.core.exceptions import ValidationError as ErroDjango
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from datetime import datetime

from usuarios.models import Atleta
from usuarios.models import Profissional
from agendamentos.models import Espaco
from agendamentos.models import Equipamento
from agendamentos.models import Agendamento
from agendamentos.models import ParticipacaoAgendamento
from agendamentos.services import criar_agendamento
from agendamentos.services import cancelar_agendamento
from agendamentos.services import inscrever_em_atividade_grupo
from agendamentos.services import cancelar_participacao as cancelar_participacao_service
from agendamentos.services import listar_horarios_profissional

from .serializers import EspacoSerializer
from .serializers import EquipamentoSerializer
from .serializers import AtletaSerializer
from .serializers import ProfissionalSerializer
from .serializers import AgendamentoSerializer
from .serializers import CriarAgendamentoSerializer
from .serializers import CancelamentoSerializer
from .serializers import InscricaoAgendamentoSerializer
from .serializers import ParticipacaoAgendamentoSerializer


class EspacoViewSet(viewsets.ModelViewSet):
    queryset = Espaco.objects.all().order_by("nome")
    serializer_class = EspacoSerializer

class EquipamentoViewSet(viewsets.ModelViewSet):
    queryset = Equipamento.objects.all().order_by("nome")
    serializer_class = EquipamentoSerializer

class AtletaViewSet(viewsets.ModelViewSet):
    queryset = Atleta.objects.all().order_by("nome")
    serializer_class = AtletaSerializer

class ProfissionalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Profissional.objects.filter(ativo=True).order_by("id")
    serializer_class = ProfissionalSerializer
    @action(detail=True, methods=["get"])
    def horarios(self, request, pk=None):
        profissional = self.get_object()

        texto_data = request.query_params.get("data")
        if not texto_data:
            return Response(
                {"data": ["Informe a data no formato AAAA-MM-DD."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = datetime.strptime(texto_data, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"data": ["Data inválida. Use o formato AAAA-MM-DD."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        horarios = listar_horarios_profissional(
            profissional=profissional,
            data=data,
        )
        return Response(horarios)

class AgendamentoViewSet(viewsets.ViewSet):
    
    def create(self, request):
        # Recebe os dados da requisição e instancia o serializer de criação.
        # O serializer será responsável por validar e converter os dados recebidos.
        serializer_entrada = CriarAgendamentoSerializer(data=request.data)

        # Verifica se os campos recebidos são válidos.
        # Caso sejam inválidos, interrompe a execução e retorna HTTP 400.
        serializer_entrada.is_valid(raise_exception=True)

        try:
            # Chama o service responsável pela criação do agendamento.
            # O service verifica as regras de negócio e salva o agendamento.
            agendamento = criar_agendamento(
                **serializer_entrada.validated_data
            )

        except ErroDjango as erro:
            # Captura erros de validação gerados pelas regras de negócio.
            # Se o erro possui mensagens associadas a campos, preserva essa estrutura.
            if hasattr(erro, "message_dict"):
                dados_erro = erro.message_dict
            else:
                # Caso contrário, organiza as mensagens em uma chave genérica.
                dados_erro = {"erro": erro.messages}

            # Retorna HTTP 400 informando por que o agendamento foi rejeitado.
            return Response(
                dados_erro,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Converte o agendamento criado em dados serializáveis para a resposta.
        serializer_saida = AgendamentoSerializer(agendamento)

        # Retorna os dados do novo agendamento com HTTP 201 (Created).
        return Response(
            serializer_saida.data,
            status=status.HTTP_201_CREATED,
        )

    
    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        # Localiza o agendamento pelo ID recebido na URL.
        # Retorna HTTP 404 caso ele não exista.
        agendamento = get_object_or_404(Agendamento, pk=pk)

        # Valida o motivo de cancelamento recebido no JSON.
        serializer_entrada = CancelamentoSerializer(data=request.data)
        serializer_entrada.is_valid(raise_exception=True)

        try:
            # Solicita ao service o cancelamento do agendamento.
            agendamento = cancelar_agendamento(
                agendamento=agendamento,
                **serializer_entrada.validated_data
            )

        except ErroDjango as erro:
            # Converte os erros de negócio em uma resposta HTTP 400.
            if hasattr(erro, "message_dict"):
                dados_erro = erro.message_dict
            else:
                dados_erro = {"erro": erro.messages}

            return Response(
                dados_erro,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Converte o agendamento atualizado em dados para a resposta.
        serializer_saida = AgendamentoSerializer(agendamento)

        return Response(
            serializer_saida.data,
            status=status.HTTP_200_OK,
        )

    
    @action(detail=True, methods=["post"])
    def inscrever(self, request, pk=None):
        # Busca o agendamento pelo ID informado na URL.
        # Caso não exista, retorna HTTP 404.
        agendamento = get_object_or_404(Agendamento, pk=pk)

        # Recebe e valida os dados da inscrição.
        serializer_entrada = InscricaoAgendamentoSerializer(
            data=request.data
        )
        serializer_entrada.is_valid(raise_exception=True)

        # Verifica se já existe uma participação desse atleta.
        # O service permite reativar uma inscrição anteriormente cancelada.
        ja_existia = agendamento.participacoes.filter(
            atleta=serializer_entrada.validated_data["atleta"]
        ).exists()

        try:
            # Chama o service responsável por realizar a inscrição.
            # O service verifica as regras de negócio e salva
            # ou reativa a participação do atleta.
            participacao = inscrever_em_atividade_grupo(
                agendamento=agendamento,
                **serializer_entrada.validated_data
            )

        except ErroDjango as erro:
            # Captura erros das regras de negócio do service.
            if hasattr(erro, "message_dict"):
                dados_erro = erro.message_dict
            else:
                dados_erro = {"erro": erro.messages}

            # Retorna HTTP 400 caso a inscrição seja rejeitada.
            return Response(
                dados_erro,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Converte a participação em dados para a resposta HTTP.
        serializer_saida = ParticipacaoAgendamentoSerializer(
            participacao
        )

        # HTTP 201 para uma nova inscrição.
        # HTTP 200 para a reativação de uma inscrição cancelada.
        codigo_status = (
            status.HTTP_200_OK
            if ja_existia
            else status.HTTP_201_CREATED
        )

        return Response(
            serializer_saida.data,
            status=codigo_status,
        )

    
    @action(
        detail=True,
        methods=["post"],
        # Extrai o id da participação diretamente do URL
        url_path=r"participacoes/(?P<participacao_id>[^/.]+)/cancelar",
        url_name="cancelar-participacao",
    )
    def cancelar_participacao(self, request, pk=None, participacao_id=None):
        # Busca a participação pelo ID informado na URL.
        # Também verifica se ela pertence ao agendamento informado.
        # Caso contrário, retorna HTTP 404.
        participacao = get_object_or_404(
            ParticipacaoAgendamento,
            pk=participacao_id,
            agendamento_id=pk,
        )

        # Recebe e valida o motivo do cancelamento.
        serializer_entrada = CancelamentoSerializer(
            data=request.data
        )
        serializer_entrada.is_valid(raise_exception=True)

        try:
            # Chama o service responsável pelo cancelamento.
            # O service aplica as regras de negócio e atualiza
            # a participação e, se necessário, o agendamento.
            agendamento = cancelar_participacao_service(
                participacao=participacao,
                **serializer_entrada.validated_data
            )

        except ErroDjango as erro:
            # Captura os erros de validação gerados pelo service.
            if hasattr(erro, "message_dict"):
                dados_erro = erro.message_dict
            else:
                dados_erro = {"erro": erro.messages}

            # Retorna HTTP 400 caso o cancelamento seja rejeitado.
            return Response(
                dados_erro,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Serializa o agendamento atualizado retornado pelo service.
        serializer_saida = AgendamentoSerializer(agendamento)

        # Retorna HTTP 200 indicando que a operação foi concluída.
        return Response(
            serializer_saida.data,
            status=status.HTTP_200_OK,
        )


