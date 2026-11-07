from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

# Models necessários para criar e consultar os dados dos testes.
from agendamentos.models import Agendamento, ParticipacaoAgendamento
from app.models import Espaco
from usuarios.models import (
    Atleta,
    DisponibilidadeProfissional,
    Funcionario,
    Profissional,
    Usuario,
)

# Testes de integração da API REST de agendamentos.
# Verificam se requisições POST com dados válidos criam agendamentos e 
# participações corretamente, retornando HTTP 201.
# Também verificam se conflitos de horário são rejeitados com HTTP 400,
# sem gerar registros indevidos no banco de dados.
# Validam a integração entre Serializer, ViewSet, Service e banco de dados.
class CriacaoAgendamentoAPITests(APITestCase):

    def setUp(self):
        # Executado ANTES de cada teste.
        # Prepara os registros necessários em um banco de testes isolado.

        # Cria uma conta de autenticação do Django para o profissional.
        conta_profissional = get_user_model().objects.create_user(
            username="profissional_api",
            password="123456",
        )

        # Associa a conta Django ao perfil de usuário do projeto.
        perfil_profissional = Usuario.objects.create(
            user=conta_profissional
        )

        # Cria o profissional que realizará os agendamentos.
        self.profissional = Profissional.objects.create(
            usuario=perfil_profissional,
            especialidade="Fisioterapia",
        )

        # Cria uma segunda conta Django, desta vez para um funcionário.
        conta_funcionario = get_user_model().objects.create_user(
            username="funcionario_api",
            password="123456",
        )

        perfil_funcionario = Usuario.objects.create(
            user=conta_funcionario
        )

        # Cria o funcionário responsável pelo registro do agendamento.
        self.funcionario = Funcionario.objects.create(
            usuario=perfil_funcionario,
            cargo="Recepcionista",
        )

        # Cria um espaço com capacidade para dois atletas.
        self.espaco = Espaco.objects.create(
            nome="Sala de teste",
            tipo="Sala",
            capacidade=2,
        )

        # Cria um atleta adulto que atende aos requisitos básicos para agendamento.
        self.atleta = Atleta.objects.create(
            nome="Atleta de teste",
            data_de_nascimento=date(2000, 1, 1),
        )

        DisponibilidadeProfissional.objects.create(
            profissional=self.profissional,
            dia_semana=0,
            hora_inicio=time(8, 0),
            hora_fim=time(12, 0),
        )

        hoje = timezone.localdate()

        # Calcula quantos dias faltam até a próxima segunda-feira.
        dias_ate_segunda = (0 - hoje.weekday()) % 7
        segunda = hoje + timedelta(days=dias_ate_segunda)

        # Define um agendamento de segunda-feira, 09:00 às 10:00.
        # make_aware() adiciona informação de fuso horário,
        # necessária para as validações do model Agendamento.
        inicio = timezone.make_aware(
            datetime.combine(segunda, time(9, 0))
        )
        fim = timezone.make_aware(
            datetime.combine(segunda, time(10, 0))
        )

        # Monta o corpo da requisição POST.
        # Os IDs serão convertidos em objetos Django pelo serializer.
        self.dados = {
            "profissional": self.profissional.id,
            "espaco": self.espaco.id,
            "atletas": [self.atleta.id],
            "registrado_por": self.funcionario.id,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "modalidade": "individual",
            "limite_participantes": 1,
        }

        # Simula autenticação na API usando a conta do funcionário.
        # Não precisa realizar login com senha neste teste.
        self.client.force_authenticate(user=conta_funcionario)

    def test_criar_agendamento_com_sucesso(self):
        # Envia uma requisição HTTP POST com os dados preparados.
        # reverse() encontra a URL pelo nome registrado no router.
        # format="json" envia os dados como JSON.
        resposta = self.client.post(
            reverse("agendamento-list"),
            self.dados,
            format="json",
        )

        # Verifica se a API respondeu com HTTP 201 (Created).
        # resposta.data será exibido se a comparação falhar,
        # ajudando a identificar o motivo do erro.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_201_CREATED,
            resposta.data,
        )

        # Verifica se exatamente um agendamento foi criado no banco.
        # Equivalente conceitual: SELECT COUNT(*) FROM agendamento;
        self.assertEqual(Agendamento.objects.count(), 1)

        # Recupera o agendamento criado para verificar seus atributos.
        agendamento = Agendamento.objects.get()

        # Confirma que o profissional e o espaço foram salvos corretamente.
        self.assertEqual(agendamento.profissional, self.profissional)
        self.assertEqual(agendamento.espaco, self.espaco)

        # Confirma que o novo agendamento está ativo.
        self.assertEqual(agendamento.situacao, "agendado")

        # Recupera a relação entre o atleta e o agendamento criado.
        participacao = ParticipacaoAgendamento.objects.get(
            agendamento=agendamento
        )

        # Confirma que o atleta correto foi inscrito.
        self.assertEqual(participacao.atleta, self.atleta)

        # Confirma que a participação foi criada como "confirmada".
        self.assertEqual(participacao.situacao, "confirmada")

    def test_rejeitar_agendamento_com_conflito(self):
        # Obtém a URL de criação de agendamentos.
        url = reverse("agendamento-list")

        # Cria o primeiro agendamento.
        primeira_resposta = self.client.post(
            url,
            self.dados,
            format="json",
        )

        # O primeiro agendamento deve ser aceito.
        self.assertEqual(
            primeira_resposta.status_code,
            status.HTTP_201_CREATED,
            primeira_resposta.data,
        )

        # Tenta criar outro agendamento com os mesmos dados:
        # mesmo profissional, mesmo horário, mesmo espaço e atleta.
        segunda_resposta = self.client.post(
            url,
            self.dados,
            format="json",
        )

        # A segunda requisição deve ser rejeitada com HTTP 400.
        # Isso verifica se a API está respeitando as validações
        # de conflito implementadas em agendamentos/services.py.
        self.assertEqual(
            segunda_resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            segunda_resposta.data,
        )

        # Confirma que a resposta contém um erro relacionado
        # ao profissional, que já está ocupado naquele horário.
        self.assertIn("profissional", segunda_resposta.data)

        # Confirma que o agendamento inválido não foi salvo.
        # A quantidade no banco deve continuar sendo exatamente 1.
        self.assertEqual(Agendamento.objects.count(), 1)
