from django.core.exceptions import ValidationError as ErroDjango
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response

from app.models import Espaco
from app.models import Equipamento
from usuarios.models import Atleta
from agendamentos.models import Agendamento
from agendamentos.services import criar_agendamento

from .serializers import EspacoSerializer
from .serializers import EquipamentoSerializer
from .serializers import AtletaSerializer
from .serializers import AgendamentoSerializer
from .serializers import CriarAgendamentoSerializer


class EspacoViewSet(viewsets.ModelViewSet):
    queryset = Espaco.objects.all().order_by("nome")
    serializer_class = EspacoSerializer

class EquipamentoViewSet(viewsets.ModelViewSet):
    queryset = Equipamento.objects.all().order_by("nome")
    serializer_class = EquipamentoSerializer

class AtletaViewSet(viewsets.ModelViewSet):
    queryset = Atleta.objects.all().order_by("nome")
    serializer_class = AtletaSerializer

class AgendamentoViewSet(viewsets.ViewSet):
    def create(self, request):
        serializer_entrada = CriarAgendamentoSerializer(data=request.data)
        serializer_entrada.is_valid(raise_exception=True)

        try:
            agendamento = criar_agendamento(
                **serializer_entrada.validated_data
            )
        except ErroDjango as erro:
            if hasattr(erro, "message_dict"):
                dados_erro = erro.message_dict
            else:
                dados_erro = {"erro": erro.messages}

            return Response(
                dados_erro,
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer_saida = AgendamentoSerializer(agendamento)

        return Response(
            serializer_saida.data,
            status=status.HTTP_201_CREATED,
        )