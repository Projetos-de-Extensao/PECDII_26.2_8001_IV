from datetime import date, datetime, time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from app.models import Equipamento, Espaco
from usuarios.models import (
    Atleta,
    DisponibilidadeProfissional,
    Funcionario,
    Profissional,
    Responsavel,
    Usuario,
)

from .models import Agendamento, ParticipacaoAgendamento
from .services import (
    cancelar_agendamento,
    cancelar_participacao,
    criar_agendamento,
)


def criar_usuario(username):
    conta = get_user_model().objects.create_user(
        username=username,
        password="SenhaTeste123!",
    )
    return Usuario.objects.create(user=conta)


class CriarAgendamentoTests(TestCase):
    def setUp(self):
        self.profissional = Profissional.objects.create(
            usuario=criar_usuario("profissional_agendamento"),
            especialidade="Fisioterapia",
        )
        self.funcionario = Funcionario.objects.create(
            usuario=criar_usuario("funcionario_agendamento"),
            cargo="Recepcionista",
        )
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
        self.equipamento = Equipamento.objects.create(
            nome="Bola suíça",
            tipo="Fisioterapia",
        )
        self.outro_equipamento = Equipamento.objects.create(
            nome="Faixa elástica",
            tipo="Fisioterapia",
        )
        self.atleta = Atleta.objects.create(
            nome="Ana",
            data_de_nascimento=date(2000, 1, 1),
        )
        self.outro_atleta = Atleta.objects.create(
            nome="Bruno",
            data_de_nascimento=date(2001, 1, 1),
        )
        DisponibilidadeProfissional.objects.create(
            profissional=self.profissional,
            dia_semana=0,
            hora_inicio=time(8, 0),
            hora_fim=time(18, 0),
        )
        self.inicio = timezone.make_aware(
            datetime(2026, 10, 26, 9, 0)
        )
        self.fim = timezone.make_aware(
            datetime(2026, 10, 26, 10, 0)
        )

    def criar(self, **alteracoes):
        dados = {
            "profissional": self.profissional,
            "espaco": self.espaco,
            "atletas": [self.atleta],
            "registrado_por": self.funcionario,
            "inicio": self.inicio,
            "fim": self.fim,
            "equipamentos": [self.equipamento],
        }
        dados.update(alteracoes)
        return criar_agendamento(**dados)

    def test_cria_agendamento_individual(self):
        agendamento = self.criar(observacoes="Primeira avaliação")

        self.assertEqual(agendamento.situacao, "agendado")
        self.assertEqual(list(agendamento.atletas.all()), [self.atleta])
        self.assertEqual(
            list(agendamento.equipamentos.all()),
            [self.equipamento],
        )
        self.assertEqual(agendamento.observacoes, "Primeira avaliação")
        participacao = agendamento.participacoes.get()
        self.assertEqual(participacao.atleta, self.atleta)
        self.assertEqual(
            participacao.situacao,
            ParticipacaoAgendamento.Situacao.CONFIRMADA,
        )

    def test_cria_agendamento_em_grupo_dentro_da_capacidade(self):
        agendamento = self.criar(
            atletas=[self.atleta, self.outro_atleta]
        )

        self.assertEqual(agendamento.atletas.count(), 2)

    def test_exige_pelo_menos_um_atleta(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar(atletas=[])

        self.assertIn("atletas", contexto.exception.message_dict)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_rejeita_atleta_repetido(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar(atletas=[self.atleta, self.atleta])

        self.assertIn("atletas", contexto.exception.message_dict)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_banco_impede_participacao_repetida(self):
        agendamento = self.criar()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ParticipacaoAgendamento.objects.create(
                    agendamento=agendamento,
                    atleta=self.atleta,
                )

        self.assertEqual(agendamento.participacoes.count(), 1)

    def test_rejeita_capacidade_excedida(self):
        terceiro = Atleta.objects.create(
            nome="Carla",
            data_de_nascimento=date(2002, 1, 1),
        )

        with self.assertRaises(ValidationError) as contexto:
            self.criar(
                atletas=[self.atleta, self.outro_atleta, terceiro]
            )

        self.assertIn("atletas", contexto.exception.message_dict)

    def test_rejeita_atleta_inativo(self):
        self.atleta.ativo = False
        self.atleta.save(update_fields=["ativo"])

        with self.assertRaises(ValidationError) as contexto:
            self.criar()

        self.assertIn("atletas", contexto.exception.message_dict)

    def test_rejeita_menor_sem_responsavel(self):
        menor = Atleta.objects.create(
            nome="Criança",
            data_de_nascimento=date(2020, 1, 1),
        )

        with self.assertRaises(ValidationError) as contexto:
            self.criar(atletas=[menor])

        self.assertIn("atletas", contexto.exception.message_dict)

    def test_aceita_menor_com_responsavel_direto(self):
        responsavel = Responsavel.objects.create(
            usuario=criar_usuario("responsavel_agendamento")
        )
        menor = Atleta.objects.create(
            nome="Criança",
            data_de_nascimento=date(2020, 1, 1),
            responsavel=responsavel,
        )

        agendamento = self.criar(atletas=[menor])

        self.assertEqual(list(agendamento.atletas.all()), [menor])

    def test_rejeita_periodo_invalido(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar(fim=self.inicio)

        self.assertIn("fim", contexto.exception.message_dict)

    def test_rejeita_horarios_sem_fuso(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar(
                inicio=datetime(2026, 10, 26, 9, 0),
                fim=datetime(2026, 10, 26, 10, 0),
            )

        self.assertIn("inicio", contexto.exception.message_dict)
        self.assertIn("fim", contexto.exception.message_dict)

    def test_rejeita_horario_fora_da_disponibilidade(self):
        inicio = timezone.make_aware(datetime(2026, 10, 26, 19, 0))
        fim = timezone.make_aware(datetime(2026, 10, 26, 20, 0))

        with self.assertRaises(ValidationError) as contexto:
            self.criar(inicio=inicio, fim=fim)

        self.assertIn("profissional", contexto.exception.message_dict)

    def test_rejeita_profissional_inativo(self):
        self.profissional.ativo = False
        self.profissional.save(update_fields=["ativo"])

        with self.assertRaises(ValidationError) as contexto:
            self.criar()

        self.assertIn("profissional", contexto.exception.message_dict)

    def test_rejeita_conflitos_dos_recursos(self):
        self.criar()

        with self.assertRaises(ValidationError) as contexto:
            self.criar()

        campos = contexto.exception.message_dict
        self.assertIn("profissional", campos)
        self.assertIn("espaco", campos)
        self.assertIn("atletas", campos)
        self.assertIn("equipamentos", campos)

    def test_horarios_adjacentes_nao_conflitam(self):
        self.criar()

        segundo = self.criar(
            inicio=self.fim,
            fim=timezone.make_aware(datetime(2026, 10, 26, 11, 0)),
        )

        self.assertEqual(Agendamento.objects.count(), 2)
        self.assertEqual(segundo.inicio, self.fim)

    def test_cancelado_nao_bloqueia_novo_agendamento(self):
        primeiro = self.criar()
        cancelar_agendamento(
            agendamento=primeiro,
            motivo="Cancelado pela recepção.",
        )

        segundo = self.criar()

        self.assertNotEqual(primeiro.pk, segundo.pk)

    def test_detecta_conflito_de_atleta_isoladamente(self):
        self.criar()

        with self.assertRaises(ValidationError) as contexto:
            self.criar(
                profissional=self._outro_profissional(),
                espaco=self.outro_espaco,
                equipamentos=[self.outro_equipamento],
            )

        self.assertEqual(
            set(contexto.exception.message_dict),
            {"atletas"},
        )

    def test_cancelar_participante_de_grupo_mantem_agendamento(self):
        primeiro = self.criar(atletas=[self.atleta, self.outro_atleta])
        participacao = primeiro.participacoes.get(atleta=self.atleta)
        cancelar_participacao(
            participacao=participacao,
            motivo="Atleta não poderá comparecer.",
        )

        primeiro.refresh_from_db()
        participacao.refresh_from_db()
        self.assertEqual(
            primeiro.situacao,
            Agendamento.Situacao.AGENDADO,
        )
        self.assertEqual(
            participacao.situacao,
            ParticipacaoAgendamento.Situacao.CANCELADA,
        )
        self.assertIsNotNone(participacao.cancelado_em)

        segundo = self.criar(
            profissional=self._outro_profissional(),
            espaco=self.outro_espaco,
            equipamentos=[self.outro_equipamento],
        )

        self.assertEqual(list(segundo.atletas.all()), [self.atleta])

    def test_cancelar_participacao_individual_cancela_agendamento(self):
        primeiro = self.criar()
        participacao = primeiro.participacoes.get()

        cancelado = cancelar_participacao(
            participacao=participacao,
            motivo="Atleta solicitou o cancelamento.",
        )

        participacao.refresh_from_db()
        self.assertEqual(
            cancelado.situacao,
            Agendamento.Situacao.CANCELADO,
        )
        self.assertEqual(
            participacao.situacao,
            ParticipacaoAgendamento.Situacao.CANCELADA,
        )
        self.assertEqual(
            cancelado.motivo_cancelamento,
            "Atleta solicitou o cancelamento.",
        )
        self.assertIsNotNone(cancelado.cancelado_em)

        segundo = self.criar()
        self.assertNotEqual(primeiro.pk, segundo.pk)

    def test_ultimo_cancelamento_do_grupo_cancela_agendamento(self):
        agendamento = self.criar(
            atletas=[self.atleta, self.outro_atleta]
        )
        cancelar_participacao(
            participacao=agendamento.participacoes.get(atleta=self.atleta)
        )

        agendamento.refresh_from_db()
        self.assertEqual(
            agendamento.situacao,
            Agendamento.Situacao.AGENDADO,
        )

        cancelar_participacao(
            participacao=agendamento.participacoes.get(
                atleta=self.outro_atleta
            )
        )

        agendamento.refresh_from_db()
        self.assertEqual(
            agendamento.situacao,
            Agendamento.Situacao.CANCELADO,
        )

    def test_cancelar_agendamento_cancela_todos_os_confirmados(self):
        agendamento = self.criar(
            atletas=[self.atleta, self.outro_atleta]
        )

        cancelado = cancelar_agendamento(
            agendamento=agendamento,
            motivo="Professor indisponível.",
        )

        self.assertEqual(
            cancelado.situacao,
            Agendamento.Situacao.CANCELADO,
        )
        self.assertEqual(
            cancelado.participacoes.filter(
                situacao=ParticipacaoAgendamento.Situacao.CANCELADA
            ).count(),
            2,
        )
        self.assertFalse(
            cancelado.participacoes.exclude(
                motivo_cancelamento="Professor indisponível."
            ).exists()
        )

    def test_nao_cancela_agendamento_realizado(self):
        agendamento = self.criar()
        agendamento.situacao = Agendamento.Situacao.REALIZADO
        agendamento.save(update_fields=["situacao"])

        with self.assertRaises(ValidationError) as contexto:
            cancelar_agendamento(agendamento=agendamento)

        self.assertIn("situacao", contexto.exception.message_dict)

    def _outro_profissional(self):
        profissional = Profissional.objects.create(
            usuario=criar_usuario("outro_profissional"),
            especialidade="Preparação física",
        )
        DisponibilidadeProfissional.objects.create(
            profissional=profissional,
            dia_semana=0,
            hora_inicio=time(8, 0),
            hora_fim=time(18, 0),
        )
        return profissional
