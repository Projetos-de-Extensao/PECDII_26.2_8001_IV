from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import DisponibilidadeProfissional, Profissional, Usuario


class ProfissionalAdminTests(TestCase):
    def setUp(self):
        self.administrador = get_user_model().objects.create_superuser(
            username="admin_profissional",
            password="SenhaTeste123!",
            email="admin@example.com",
        )
        conta_profissional = get_user_model().objects.create_user(
            username="profissional_com_horario",
        )
        self.usuario_profissional = Usuario.objects.create(
            user=conta_profissional
        )
        self.client.force_login(self.administrador)

    def dados_formulario(self):
        return {
            "usuario": self.usuario_profissional.id,
            "especialidade": "Treinamento funcional",
            "ativo": "on",
            "disponibilidades-TOTAL_FORMS": "1",
            "disponibilidades-INITIAL_FORMS": "0",
            "disponibilidades-MIN_NUM_FORMS": "0",
            "disponibilidades-MAX_NUM_FORMS": "1000",
            "disponibilidades-0-dia_semana": "0",
            "disponibilidades-0-hora_inicio": "08:00",
            "disponibilidades-0-hora_fim": "12:00",
            "_save": "Salvar",
        }

    def test_tela_de_profissional_exibe_horarios_disponiveis(self):
        resposta = self.client.get(
            reverse("admin:usuarios_profissional_add")
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Horários disponíveis")
        self.assertContains(
            resposta,
            'name="disponibilidades-0-dia_semana"',
            html=False,
        )
        self.assertContains(
            resposta,
            '<option value="07:30">07:30</option>',
            html=False,
        )
        self.assertContains(
            resposta,
            '<option value="20:00">20:00</option>',
            html=False,
        )
        self.assertNotContains(
            resposta,
            '<option value="06:30">06:30</option>',
            html=False,
        )
        self.assertNotContains(
            resposta,
            '<option value="12:30">12:30</option>',
            html=False,
        )

    def test_cadastra_profissional_e_disponibilidade_juntos(self):
        resposta = self.client.post(
            reverse("admin:usuarios_profissional_add"),
            self.dados_formulario(),
        )

        profissional = Profissional.objects.get(
            usuario=self.usuario_profissional
        )
        disponibilidade = DisponibilidadeProfissional.objects.get(
            profissional=profissional
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(disponibilidade.dia_semana, 0)
        self.assertEqual(disponibilidade.hora_inicio.isoformat(), "08:00:00")
        self.assertEqual(disponibilidade.hora_fim.isoformat(), "12:00:00")
