from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

# Models necessários para criar e consultar os dados dos testes.
from agendamentos.models import Agendamento
from app.models import Equipamento, Espaco
from usuarios.models import (
    Atleta,
    DisponibilidadeProfissional,
    Funcionario,
    Profissional,
    Responsavel,
    Usuario,
)


# Testes de integração das regras que envolvem Atleta, Espaço e
# Equipamento na criação de agendamentos (agendamentos/services.py).
# Verificam capacidade do espaço, reserva de equipamentos e requisitos
# do atleta, sempre pelo endpoint POST /agendamentos/.
class RecursosAgendamentoAPITests(APITestCase):

    def _criar_profissional(self, username):
        # Cria a cadeia completa: conta Django -> Usuario -> Profissional,
        # com disponibilidade na segunda-feira, das 08:00 às 12:00.
        conta = get_user_model().objects.create_user(
            username=username,
            password="123456",
        )
        perfil = Usuario.objects.create(user=conta)
        profissional = Profissional.objects.create(
            usuario=perfil,
            especialidade="Fisioterapia",
        )
        DisponibilidadeProfissional.objects.create(
            profissional=profissional,
            dia_semana=0,
            hora_inicio=time(8, 0),
            hora_fim=time(12, 0),
        )
        return profissional

    def _horario(self, hora_inicio, hora_fim):
        # Devolve início e fim (ISO 8601) na próxima segunda-feira.
        # make_aware() adiciona informação de fuso horário.
        inicio = timezone.make_aware(
            datetime.combine(self.segunda, hora_inicio)
        )
        fim = timezone.make_aware(
            datetime.combine(self.segunda, hora_fim)
        )
        return inicio.isoformat(), fim.isoformat()

    def _dados(self, **alteracoes):
        # Copia os dados válidos do setUp(), aplicando as alterações
        # pedidas, sem modificar os dados dos outros testes.
        dados = self.dados.copy()
        dados.update(alteracoes)
        return dados

    def setUp(self):
        # Executado ANTES de cada teste.
        # Prepara os registros necessários em um banco de testes isolado.

        # Cria dois profissionais, para permitir agendamentos simultâneos.
        self.profissional = self._criar_profissional("profissional_recursos")
        self.outro_profissional = self._criar_profissional(
            "outro_profissional_recursos"
        )

        # Cria o funcionário responsável pelo registro dos agendamentos.
        conta_funcionario = get_user_model().objects.create_user(
            username="funcionario_recursos",
            password="123456",
        )
        perfil_funcionario = Usuario.objects.create(user=conta_funcionario)
        self.funcionario = Funcionario.objects.create(
            usuario=perfil_funcionario,
            cargo="Recepcionista",
        )

        # Cria dois espaços com capacidade para dois atletas cada.
        self.espaco = Espaco.objects.create(
            nome="Sala 1",
            tipo="Sala",
            capacidade=2,
        )
        self.outro_espaco = Espaco.objects.create(
            nome="Sala 2",
            tipo="Sala",
            capacidade=2,
        )

        # Cria dois atletas adultos.
        self.atleta = Atleta.objects.create(
            nome="Atleta de teste",
            data_de_nascimento=date(2000, 1, 1),
        )
        self.outro_atleta = Atleta.objects.create(
            nome="Outro atleta",
            data_de_nascimento=date(2000, 1, 1),
        )

        # Cria um equipamento que poderá ser reservado.
        self.equipamento = Equipamento.objects.create(
            nome="Colchonete",
            tipo="Fisioterapia",
        )

        # Calcula quantos dias faltam até a próxima segunda-feira.
        hoje = timezone.localdate()
        dias_ate_segunda = (0 - hoje.weekday()) % 7
        self.segunda = hoje + timedelta(days=dias_ate_segunda)

        # Define um agendamento de segunda-feira, 09:00 às 10:00.
        inicio, fim = self._horario(time(9, 0), time(10, 0))

        # Monta o corpo da requisição POST.
        self.dados = {
            "profissional": self.profissional.id,
            "espaco": self.espaco.id,
            "atletas": [self.atleta.id],
            "registrado_por": self.funcionario.id,
            "inicio": inicio,
            "fim": fim,
            "modalidade": "individual",
            "limite_participantes": 1,
        }

        # Simula autenticação na API usando a conta do funcionário.
        self.client.force_authenticate(user=conta_funcionario)


    # ------------------------------------------------------------------
    # Equipamento
    # ------------------------------------------------------------------

    def test_criar_agendamento_com_equipamento(self):
        resposta = self.client.post(
            reverse("agendamento-list"),
            self._dados(equipamentos=[self.equipamento.id]),
            format="json",
        )

        # Verifica se a API respondeu com HTTP 201 (Created).
        self.assertEqual(
            resposta.status_code,
            status.HTTP_201_CREATED,
            resposta.data,
        )

        # Confirma que o equipamento foi vinculado ao agendamento.
        agendamento = Agendamento.objects.get(pk=resposta.data["id"])
        self.assertEqual(
            list(agendamento.equipamentos.all()),
            [self.equipamento],
        )

        # Confirma que a resposta também informa o equipamento.
        self.assertEqual(
            resposta.data["equipamentos"],
            [self.equipamento.id],
        )


    def test_rejeitar_equipamento_ja_reservado_no_mesmo_horario(self):
        url = reverse("agendamento-list")

        # Reserva o equipamento das 09:00 às 10:00.
        primeira_resposta = self.client.post(
            url,
            self._dados(equipamentos=[self.equipamento.id]),
            format="json",
        )
        self.assertEqual(
            primeira_resposta.status_code,
            status.HTTP_201_CREATED,
            primeira_resposta.data,
        )

        # Tenta reservar o mesmo equipamento no mesmo horário.
        # Profissional, espaço e atleta são outros, para que o único
        # conflito seja o do equipamento.
        segunda_resposta = self.client.post(
            url,
            self._dados(
                profissional=self.outro_profissional.id,
                espaco=self.outro_espaco.id,
                atletas=[self.outro_atleta.id],
                equipamentos=[self.equipamento.id],
            ),
            format="json",
        )

        # A segunda requisição deve ser rejeitada com HTTP 400.
        self.assertEqual(
            segunda_resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            segunda_resposta.data,
        )

        # Confirma que o erro aponta para os equipamentos
        # e que ele é o único problema encontrado.
        self.assertIn("equipamentos", segunda_resposta.data)
        self.assertEqual(list(segunda_resposta.data.keys()), ["equipamentos"])

        # Confirma que o agendamento inválido não foi salvo.
        self.assertEqual(Agendamento.objects.count(), 1)


    def test_permitir_mesmo_equipamento_em_horario_seguinte(self):
        url = reverse("agendamento-list")

        # Reserva o equipamento das 09:00 às 10:00.
        primeira_resposta = self.client.post(
            url,
            self._dados(equipamentos=[self.equipamento.id]),
            format="json",
        )
        self.assertEqual(
            primeira_resposta.status_code,
            status.HTTP_201_CREATED,
            primeira_resposta.data,
        )

        # Reserva o mesmo equipamento das 10:00 às 11:00.
        # O fim de um agendamento coincide com o início do outro,
        # o que não é sobreposição.
        inicio, fim = self._horario(time(10, 0), time(11, 0))
        segunda_resposta = self.client.post(
            url,
            self._dados(
                atletas=[self.outro_atleta.id],
                equipamentos=[self.equipamento.id],
                inicio=inicio,
                fim=fim,
            ),
            format="json",
        )

        self.assertEqual(
            segunda_resposta.status_code,
            status.HTTP_201_CREATED,
            segunda_resposta.data,
        )
        self.assertEqual(Agendamento.objects.count(), 2)


    def test_liberar_equipamento_apos_cancelar_agendamento(self):
        url = reverse("agendamento-list")

        # Reserva o equipamento das 09:00 às 10:00.
        primeira_resposta = self.client.post(
            url,
            self._dados(equipamentos=[self.equipamento.id]),
            format="json",
        )
        self.assertEqual(
            primeira_resposta.status_code,
            status.HTTP_201_CREATED,
            primeira_resposta.data,
        )

        # Cancela o agendamento que reservava o equipamento.
        resposta_cancelamento = self.client.post(
            reverse(
                "agendamento-cancelar",
                args=[primeira_resposta.data["id"]],
            ),
            {"motivo": "Atleta não poderá comparecer."},
            format="json",
        )
        self.assertEqual(
            resposta_cancelamento.status_code,
            status.HTTP_200_OK,
            resposta_cancelamento.data,
        )

        # Reserva o mesmo equipamento, no mesmo horário, outra vez.
        # Agendamentos cancelados não devem bloquear o equipamento.
        segunda_resposta = self.client.post(
            url,
            self._dados(equipamentos=[self.equipamento.id]),
            format="json",
        )

        self.assertEqual(
            segunda_resposta.status_code,
            status.HTTP_201_CREATED,
            segunda_resposta.data,
        )


    # ------------------------------------------------------------------
    # Espaço
    # ------------------------------------------------------------------

    def test_rejeitar_agendamento_com_espaco_lotado(self):
        url = reverse("agendamento-list")

        # Reserva as duas vagas do espaço (capacidade 2) em grupo.
        primeira_resposta = self.client.post(
            url,
            self._dados(modalidade="grupo", limite_participantes=2),
            format="json",
        )
        self.assertEqual(
            primeira_resposta.status_code,
            status.HTTP_201_CREATED,
            primeira_resposta.data,
        )

        # Tenta usar o mesmo espaço, no mesmo horário, com outro
        # profissional e outro atleta. Já há 2 vagas reservadas,
        # então não cabe mais ninguém.
        segunda_resposta = self.client.post(
            url,
            self._dados(
                profissional=self.outro_profissional.id,
                atletas=[self.outro_atleta.id],
            ),
            format="json",
        )

        self.assertEqual(
            segunda_resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            segunda_resposta.data,
        )

        # Confirma que o erro aponta para o espaço.
        self.assertIn("espaco", segunda_resposta.data)

        # Confirma que o agendamento inválido não foi salvo.
        self.assertEqual(Agendamento.objects.count(), 1)


    def test_permitir_espaco_com_vaga_restante(self):
        url = reverse("agendamento-list")

        # Reserva uma vaga de um espaço com capacidade 2.
        primeira_resposta = self.client.post(
            url,
            self.dados,
            format="json",
        )
        self.assertEqual(
            primeira_resposta.status_code,
            status.HTTP_201_CREATED,
            primeira_resposta.data,
        )

        # A vaga restante pode ser usada por outro profissional.
        segunda_resposta = self.client.post(
            url,
            self._dados(
                profissional=self.outro_profissional.id,
                atletas=[self.outro_atleta.id],
            ),
            format="json",
        )

        self.assertEqual(
            segunda_resposta.status_code,
            status.HTTP_201_CREATED,
            segunda_resposta.data,
        )
        self.assertEqual(Agendamento.objects.count(), 2)


    def test_rejeitar_limite_maior_que_a_capacidade_do_espaco(self):
        # O espaço comporta 2 atletas, mas o grupo pede 3 vagas.
        resposta = self.client.post(
            reverse("agendamento-list"),
            self._dados(modalidade="grupo", limite_participantes=3),
            format="json",
        )

        self.assertEqual(
            resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            resposta.data,
        )

        # Confirma que nada foi salvo.
        self.assertEqual(Agendamento.objects.count(), 0)


    # ------------------------------------------------------------------
    # Atleta
    # ------------------------------------------------------------------

    def test_rejeitar_agendamento_de_atleta_inativo(self):
        # Desativa o atleta antes de tentar agendar.
        self.atleta.ativo = False
        self.atleta.save(update_fields=["ativo"])

        resposta = self.client.post(
            reverse("agendamento-list"),
            self.dados,
            format="json",
        )

        self.assertEqual(
            resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            resposta.data,
        )

        # Confirma que o erro aponta para os atletas.
        self.assertIn("atletas", resposta.data)
        self.assertEqual(Agendamento.objects.count(), 0)


    def test_rejeitar_agendamento_de_menor_sem_responsavel(self):
        # Atleta com cerca de 10 anos e sem responsável vinculado.
        menor = Atleta.objects.create(
            nome="Atleta menor",
            data_de_nascimento=timezone.localdate() - timedelta(days=3653),
        )

        resposta = self.client.post(
            reverse("agendamento-list"),
            self._dados(atletas=[menor.id]),
            format="json",
        )

        self.assertEqual(
            resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            resposta.data,
        )

        # Confirma que o erro aponta para os atletas.
        self.assertIn("atletas", resposta.data)
        self.assertEqual(Agendamento.objects.count(), 0)


    def test_permitir_agendamento_de_menor_com_responsavel(self):
        # Cria o responsável: conta Django -> Usuario -> Responsavel.
        conta_responsavel = get_user_model().objects.create_user(
            username="responsavel_recursos",
            password="123456",
        )
        responsavel = Responsavel.objects.create(
            usuario=Usuario.objects.create(user=conta_responsavel)
        )

        # Atleta com cerca de 10 anos, agora com responsável vinculado.
        menor = Atleta.objects.create(
            nome="Atleta menor",
            data_de_nascimento=timezone.localdate() - timedelta(days=3653),
            responsavel=responsavel,
        )

        resposta = self.client.post(
            reverse("agendamento-list"),
            self._dados(atletas=[menor.id]),
            format="json",
        )

        self.assertEqual(
            resposta.status_code,
            status.HTTP_201_CREATED,
            resposta.data,
        )
        self.assertEqual(Agendamento.objects.count(), 1)
