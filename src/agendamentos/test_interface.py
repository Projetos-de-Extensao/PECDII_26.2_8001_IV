from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from app.models import Equipamento, Espaco
from usuarios.models import (
    Atleta,
    DisponibilidadeProfissional,
    Funcionario,
    Profissional,
    Usuario,
)

from .models import Agendamento, ParticipacaoAgendamento


def criar_perfil(username, *, staff=False):
    conta = get_user_model().objects.create_user(
        username=username,
        password="SenhaTeste123!",
        is_staff=staff,
    )
    return Usuario.objects.create(user=conta)


class InterfaceAgendamentosTests(TestCase):
    def setUp(self):
        perfil_staff = criar_perfil("operador_interface", staff=True)
        self.conta_staff = perfil_staff.user
        self.funcionario = Funcionario.objects.create(
            usuario=perfil_staff,
            cargo="Recepcionista",
        )
        self.profissional = Profissional.objects.create(
            usuario=criar_perfil("profissional_interface"),
            especialidade="Treinamento",
        )
        self.espaco = Espaco.objects.create(
            nome="Quadra teste",
            tipo="Quadra",
            capacidade=3,
        )
        self.atleta = Atleta.objects.create(
            nome="Atleta da interface",
            data_de_nascimento=date(2000, 1, 1),
        )
        self.outro_atleta = Atleta.objects.create(
            nome="Segundo atleta",
            data_de_nascimento=date(2001, 1, 1),
        )
        self.equipamento = Equipamento.objects.create(
            nome="Cone",
            tipo="Treino",
        )
        DisponibilidadeProfissional.objects.create(
            profissional=self.profissional,
            dia_semana=0,
            hora_inicio=time(8, 0),
            hora_fim=time(18, 0),
        )

    def dados_formulario(self):
        return {
            "profissional": self.profissional.id,
            "espaco": self.espaco.id,
            "atletas": [self.atleta.id],
            "equipamentos": [self.equipamento.id],
            "registrado_por": self.funcionario.id,
            "data": "2026-10-26",
            "inicio": "2026-10-26T14:00",
            "fim": "2026-10-26T14:30",
            "modalidade": Agendamento.Modalidade.INDIVIDUAL,
            "limite_participantes": 1,
            "agendamento_grupo": "",
            "observacoes": "Criado pela tela de teste",
        }

    def dados_cadastro_rapido(self):
        dados = self.dados_formulario()
        dados.update({
            "atletas": [],
            "novo_atleta": "on",
            "novo_atleta_nome": "Novo Interessado",
            "novo_atleta_email": "interessado@example.com",
            "novo_atleta_telefone": "(11) 99999-7777",
            "novo_atleta_data_de_nascimento": "2000-05-10",
        })
        return dados

    def test_exige_login_de_staff(self):
        resposta = self.client.get(reverse("agendamentos:lista"))

        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("admin:login"), resposta.url)

    def test_staff_consegue_abrir_formulario(self):
        self.client.force_login(self.conta_staff)

        resposta = self.client.get(reverse("agendamentos:novo"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Novo agendamento")
        self.assertContains(resposta, self.atleta.nome)
        self.assertContains(resposta, "Escolha o horário")
        self.assertContains(
            resposta,
            "Atendimentos das 07:00 às 12:00 e das 13:00 às 20:00.",
        )
        self.assertContains(resposta, "Aula Experimental")
        self.assertNotContains(resposta, "Cadastrar novo interessado")
        self.assertNotContains(
            resposta,
            "Selecione para menores de 18 anos",
        )

    def test_cadastro_rapido_cria_interessado_e_experimental(self):
        self.client.force_login(self.conta_staff)

        resposta = self.client.post(
            reverse("agendamentos:novo"),
            self.dados_cadastro_rapido(),
        )

        interessado = Atleta.objects.get(nome="Novo Interessado")
        participacao = ParticipacaoAgendamento.objects.get(
            atleta=interessado
        )
        self.assertRedirects(
            resposta,
            reverse(
                "agendamentos:detalhe",
                args=[participacao.agendamento_id],
            ),
        )
        self.assertEqual(interessado.email, "interessado@example.com")
        self.assertEqual(interessado.telefone, "(11) 99999-7777")
        self.assertIsNone(interessado.usuario)
        self.assertEqual(
            participacao.tipo,
            ParticipacaoAgendamento.Tipo.EXPERIMENTAL,
        )
        self.assertEqual(participacao.registrado_por, self.funcionario)

    def test_cadastro_rapido_inscreve_experimental_em_grupo(self):
        self.client.force_login(self.conta_staff)
        dados_grupo = self.dados_formulario()
        dados_grupo.update({
            "modalidade": Agendamento.Modalidade.GRUPO,
            "limite_participantes": 3,
        })
        self.client.post(reverse("agendamentos:novo"), dados_grupo)
        grupo = Agendamento.objects.get()

        dados = self.dados_cadastro_rapido()
        dados.update({
            "agendamento_grupo": grupo.id,
            "espaco": "",
        })
        resposta = self.client.post(reverse("agendamentos:novo"), dados)

        interessado = Atleta.objects.get(nome="Novo Interessado")
        participacao = grupo.participacoes.get(atleta=interessado)
        self.assertRedirects(
            resposta,
            reverse("agendamentos:detalhe", args=[grupo.id]),
        )
        self.assertEqual(
            participacao.tipo,
            ParticipacaoAgendamento.Tipo.EXPERIMENTAL,
        )

    def test_cadastro_rapido_nao_salva_atleta_se_agendamento_falhar(self):
        self.client.force_login(self.conta_staff)
        self.client.post(
            reverse("agendamentos:novo"),
            self.dados_formulario(),
        )
        quantidade_inicial = Atleta.objects.count()

        resposta = self.client.post(
            reverse("agendamentos:novo"),
            self.dados_cadastro_rapido(),
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(
            resposta,
            "O profissional já possui um agendamento nesse horário.",
        )
        self.assertEqual(Atleta.objects.count(), quantidade_inicial)

    def test_cadastro_rapido_exige_responsavel_para_menor(self):
        self.client.force_login(self.conta_staff)
        dados = self.dados_cadastro_rapido()
        dados["novo_atleta_data_de_nascimento"] = "2015-05-10"

        resposta = self.client.post(reverse("agendamentos:novo"), dados)

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(
            resposta,
            "Para menores de 18 anos, faça primeiro o cadastro completo "
            "do atleta e do responsável.",
        )
        self.assertFalse(
            Atleta.objects.filter(nome="Novo Interessado").exists()
        )

    def test_detalhe_identifica_participacao_experimental(self):
        self.client.force_login(self.conta_staff)
        resposta = self.client.post(
            reverse("agendamentos:novo"),
            self.dados_cadastro_rapido(),
        )
        agendamento = ParticipacaoAgendamento.objects.get().agendamento

        resposta = self.client.get(
            reverse("agendamentos:detalhe", args=[agendamento.id])
        )

        self.assertContains(resposta, "Experimental")
        self.assertContains(resposta, "Registrado por:")

    def test_formulario_cria_agendamento_pelo_servico(self):
        self.client.force_login(self.conta_staff)

        resposta = self.client.post(
            reverse("agendamentos:novo"),
            self.dados_formulario(),
        )

        agendamento = Agendamento.objects.get()
        self.assertRedirects(
            resposta,
            reverse("agendamentos:detalhe", args=[agendamento.id]),
        )
        self.assertEqual(agendamento.registrado_por, self.funcionario)
        self.assertEqual(
            list(agendamento.atletas.all()),
            [self.atleta],
        )

    def test_formulario_exibe_conflito_sem_criar_segundo(self):
        self.client.force_login(self.conta_staff)
        self.client.post(
            reverse("agendamentos:novo"),
            self.dados_formulario(),
        )

        resposta = self.client.post(
            reverse("agendamentos:novo"),
            self.dados_formulario(),
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(
            resposta,
            "O profissional já possui um agendamento nesse horário.",
        )
        self.assertEqual(Agendamento.objects.count(), 1)

    def test_endpoint_mostra_blocos_de_trinta_minutos(self):
        self.client.force_login(self.conta_staff)

        resposta = self.client.get(
            reverse("agendamentos:horarios"),
            {
                "profissional": self.profissional.id,
                "data": "2026-10-26",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        horarios = resposta.json()["horarios"]
        self.assertIn("14:00", [item["rotulo"] for item in horarios])
        self.assertTrue(
            next(item for item in horarios if item["rotulo"] == "14:00")[
                "disponivel"
            ]
        )
        rotulos = [item["rotulo"] for item in horarios]
        self.assertNotIn("12:00", rotulos)
        self.assertNotIn("12:30", rotulos)

    def test_formulario_inscreve_em_grupo_existente(self):
        self.client.force_login(self.conta_staff)
        dados_grupo = self.dados_formulario()
        dados_grupo.update({
            "modalidade": Agendamento.Modalidade.GRUPO,
            "limite_participantes": 3,
        })
        self.client.post(reverse("agendamentos:novo"), dados_grupo)
        grupo = Agendamento.objects.get()

        dados_inscricao = self.dados_formulario()
        dados_inscricao.update({
            "atletas": [self.outro_atleta.id],
            "espaco": "",
            "registrado_por": "",
            "agendamento_grupo": grupo.id,
        })
        resposta = self.client.post(
            reverse("agendamentos:novo"),
            dados_inscricao,
        )

        self.assertRedirects(
            resposta,
            reverse("agendamentos:detalhe", args=[grupo.id]),
        )
        self.assertEqual(Agendamento.objects.count(), 1)
        self.assertEqual(grupo.participacoes.count(), 2)

        resposta_horarios = self.client.get(
            reverse("agendamentos:horarios"),
            {
                "profissional": self.profissional.id,
                "data": "2026-10-26",
            },
        )
        bloco = next(
            item
            for item in resposta_horarios.json()["horarios"]
            if item["rotulo"] == "14:00"
        )
        self.assertEqual(bloco["tipo"], "grupo")
        self.assertEqual((bloco["inscritos"], bloco["limite"]), (2, 3))

    def test_tela_cancela_participacao_e_agendamento_individual(self):
        self.client.force_login(self.conta_staff)
        self.client.post(
            reverse("agendamentos:novo"),
            self.dados_formulario(),
        )
        participacao = ParticipacaoAgendamento.objects.get()

        resposta = self.client.post(
            reverse(
                "agendamentos:cancelar_participacao",
                args=[participacao.id],
            ),
            {"motivo": "Aluno avisou"},
        )

        participacao.refresh_from_db()
        participacao.agendamento.refresh_from_db()
        self.assertRedirects(
            resposta,
            reverse(
                "agendamentos:detalhe",
                args=[participacao.agendamento_id],
            ),
        )
        self.assertEqual(
            participacao.situacao,
            ParticipacaoAgendamento.Situacao.CANCELADA,
        )
        self.assertEqual(
            participacao.agendamento.situacao,
            Agendamento.Situacao.CANCELADO,
        )
