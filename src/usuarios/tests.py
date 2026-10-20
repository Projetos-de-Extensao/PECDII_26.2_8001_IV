
from datetime import date, time
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone

from .models import (
    Atleta,
    DisponibilidadeProfissional,
    Funcionario,
    Profissional,
    Responsavel,
    Usuario,
)


def criar_perfil(username):
    """Cria uma conta Django associada a um perfil Usuario."""
    conta = get_user_model().objects.create_user(
        username=username,
        password="SenhaTeste123!"
    )
    return Usuario.objects.create(user=conta)


class UsuarioTests(TestCase):

    def setUp(self):
        self.conta = get_user_model().objects.create_user(
            username="teste",
            password="SenhaTeste123!"
        )

    def test_telefone_valido(self):
        perfil = Usuario(
            user=self.conta,
            telefone="(21) 99999-8888"
        )
        perfil.full_clean()

    def test_telefone_invalido(self):
        perfil = Usuario(
            user=self.conta,
            telefone="219999"
        )

        with self.assertRaises(ValidationError) as contexto:
            perfil.full_clean()

        self.assertIn(
            "telefone",
            contexto.exception.message_dict
        )

    def test_telefone_opcional(self):
        perfil = Usuario(
            user=self.conta,
            telefone=""
        )
        perfil.full_clean()


class AtletaTests(TestCase):

    def setUp(self):
        self.contador = 0

        perfil = criar_perfil("responsavel_atleta")
        self.responsavel = Responsavel.objects.create(
            usuario=perfil
        )

    def criar_atleta(
        self,
        nascimento=None,
        *,
        usuario=None,
        nome=None,
        responsavel=None
    ):
        self.contador += 1

        return Atleta(
            nome=nome or f"Atleta {self.contador}",
            usuario=usuario,
            data_de_nascimento=nascimento,
            responsavel=responsavel
        )

    def test_cadastro_sem_login_e_nascimento(self):
        atleta = self.criar_atleta()

        atleta.full_clean()
        atleta.save()

        self.assertIsNone(atleta.usuario)
        self.assertIsNone(atleta.idade)

    def test_cadastro_menor_sem_responsavel_permitido_inicialmente(self):
        nascimento = date(
            timezone.localdate().year - 10, 1, 1
        )
        atleta = self.criar_atleta(nascimento)

        atleta.full_clean()
        atleta.save()

        self.assertIsNone(atleta.responsavel)

    def test_menor_sem_responsavel_nao_pode_agendar(self):
        nascimento = date(
            timezone.localdate().year - 10, 1, 1
        )
        atleta = self.criar_atleta(nascimento)
        atleta.save()

        with self.assertRaises(ValidationError) as contexto:
            atleta.validar_para_agendamento()

        self.assertIn(
            "responsavel",
            contexto.exception.message_dict
        )

    def test_menor_com_responsavel_pode_agendar(self):
        nascimento = date(
            timezone.localdate().year - 10, 1, 1
        )

        atleta = self.criar_atleta(
            nascimento,
            responsavel=self.responsavel
        )
        atleta.save()

        atleta.validar_para_agendamento()

    def test_maior_sem_responsavel_pode_agendar(self):
        nascimento = date(
            timezone.localdate().year - 25, 1, 1
        )
        atleta = self.criar_atleta(nascimento)
        atleta.save()

        atleta.validar_para_agendamento()

    def test_nascimento_futuro(self):
        nascimento = date(
            timezone.localdate().year + 1, 1, 1
        )
        atleta = self.criar_atleta(nascimento)

        with self.assertRaises(ValidationError) as contexto:
            atleta.full_clean()

        self.assertIn(
            "data_de_nascimento",
            contexto.exception.message_dict
        )

    def test_agendamento_exige_data_de_nascimento(self):
        atleta = self.criar_atleta()
        atleta.save()

        with self.assertRaises(ValidationError) as contexto:
            atleta.validar_para_agendamento()

        self.assertIn(
            "data_de_nascimento",
            contexto.exception.message_dict
        )

    def test_agendamento_exige_atleta_salvo(self):
        nascimento = date(
            timezone.localdate().year - 25, 1, 1
        )
        atleta = self.criar_atleta(nascimento)

        with self.assertRaises(ValidationError) as contexto:
            atleta.validar_para_agendamento()

        self.assertIn(
            "__all__",
            contexto.exception.message_dict
        )

    def test_nome_obrigatorio(self):
        atleta = Atleta(nome="")

        with self.assertRaises(ValidationError) as contexto:
            atleta.full_clean()

        self.assertIn(
            "nome",
            contexto.exception.message_dict
        )

    def test_telefone_invalido(self):
        atleta = self.criar_atleta()
        atleta.telefone = "123"

        with self.assertRaises(ValidationError) as contexto:
            atleta.full_clean()

        self.assertIn(
            "telefone",
            contexto.exception.message_dict
        )

    def test_idade_no_dia_do_aniversario_de_18(self):
        atleta = self.criar_atleta(date(2008, 10, 20))

        with patch(
            "usuarios.models.timezone.localdate",
            return_value=date(2026, 10, 20)
        ):
            self.assertEqual(atleta.idade, 18)

    def test_idade_um_dia_antes_do_aniversario_de_18(self):
        atleta = self.criar_atleta(date(2008, 10, 20))

        with patch(
            "usuarios.models.timezone.localdate",
            return_value=date(2026, 10, 19)
        ):
            self.assertEqual(atleta.idade, 17)

    def test_usuario_nao_pode_ter_dois_perfis_atleta(self):
        perfil = criar_perfil("atleta_conta")

        atleta1 = self.criar_atleta(usuario=perfil)
        atleta1.full_clean()
        atleta1.save()

        atleta2 = self.criar_atleta(usuario=perfil)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                atleta2.save()

        self.assertEqual(Atleta.objects.count(), 1)

    def test_varios_atletas_sem_login_sao_permitidos(self):
        self.criar_atleta().save()
        self.criar_atleta().save()

        self.assertEqual(
            Atleta.objects.filter(
                usuario__isnull=True
            ).count(),
            2
        )


class ResponsavelTests(TestCase):

    def setUp(self):
        self.perfil1 = criar_perfil("responsavel_maria")
        self.perfil2 = criar_perfil("responsavel_carlos")

        self.responsavel1 = Responsavel.objects.create(
            usuario=self.perfil1
        )
        self.responsavel2 = Responsavel.objects.create(
            usuario=self.perfil2
        )

    def test_responsavel_pode_ter_varios_atletas(self):
        Atleta.objects.create(
            nome="João",
            responsavel=self.responsavel1
        )
        Atleta.objects.create(
            nome="Ana",
            responsavel=self.responsavel1
        )

        self.assertEqual(
            self.responsavel1.atletas.count(),
            2
        )

    def test_atleta_possui_apenas_um_responsavel(self):
        atleta = Atleta.objects.create(
            nome="João",
            responsavel=self.responsavel1
        )

        self.assertEqual(
            atleta.responsavel,
            self.responsavel1
        )

        atleta.responsavel = self.responsavel2
        atleta.save(update_fields=["responsavel"])

        self.assertEqual(
            atleta.responsavel,
            self.responsavel2
        )

        self.assertFalse(
            self.responsavel1.atletas.filter(
                pk=atleta.pk
            ).exists()
        )

        self.assertEqual(
            Atleta.objects.count(),
            1
        )

    def test_protect_impede_exclusao_de_responsavel_vinculado(self):
        Atleta.objects.create(
            nome="João",
            responsavel=self.responsavel1
        )

        with self.assertRaises(ProtectedError):
            self.responsavel1.delete()

    def test_responsavel_exige_usuario(self):
        responsavel = Responsavel()

        with self.assertRaises(ValidationError) as contexto:
            responsavel.full_clean()

        self.assertIn(
            "usuario",
            contexto.exception.message_dict
        )

    def test_responsavel_telefone_invalido(self):
        responsavel = Responsavel(
            usuario=criar_perfil("telefone_invalido"),
            telefone="1234567"
        )

        with self.assertRaises(ValidationError) as contexto:
            responsavel.full_clean()

        self.assertIn(
            "telefone",
            contexto.exception.message_dict
        )

    def test_responsavel_telefone_valido(self):
        responsavel = Responsavel(
            usuario=criar_perfil("telefone_valido"),
            telefone="(21) 99999-8888"
        )

        responsavel.full_clean()
        responsavel.save()

        self.assertEqual(
            responsavel.telefone,
            "(21) 99999-8888"
        )

    def test_usuario_nao_pode_ter_dois_perfis_responsavel(self):
        outro_responsavel = Responsavel(
            usuario=self.perfil1
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                outro_responsavel.save()

        self.assertEqual(
            Responsavel.objects.count(),
            2
        )


class ProfissionalTests(TestCase):

    def setUp(self):
        self.usuario = criar_perfil("profissional_teste")

    def test_profissional_valido(self):
        profissional = Profissional(
            usuario=self.usuario,
            especialidade="Basquete"
        )

        profissional.full_clean()
        profissional.save()

        self.assertEqual(
            profissional.especialidade,
            "Basquete"
        )

    def test_profissional_sem_especialidade(self):
        profissional = Profissional(
            usuario=self.usuario,
            especialidade=""
        )

        with self.assertRaises(ValidationError) as contexto:
            profissional.full_clean()

        self.assertIn(
            "especialidade",
            contexto.exception.message_dict
        )


class FuncionarioTests(TestCase):

    def setUp(self):
        self.usuario = criar_perfil("funcionario_teste")

    def test_funcionario_valido(self):
        funcionario = Funcionario(
            usuario=self.usuario,
            cargo="Recepcionista"
        )

        funcionario.full_clean()
        funcionario.save()

        self.assertEqual(
            funcionario.cargo,
            "Recepcionista"
        )

    def test_funcionario_sem_cargo(self):
        funcionario = Funcionario(
            usuario=self.usuario,
            cargo=""
        )

        with self.assertRaises(ValidationError) as contexto:
            funcionario.full_clean()

        self.assertIn(
            "cargo",
            contexto.exception.message_dict
        )


class DisponibilidadeProfissionalTests(TestCase):

    def setUp(self):
        perfil = criar_perfil("profissional_agenda")
        self.profissional = Profissional.objects.create(
            usuario=perfil,
            especialidade="Fisioterapia"
        )

    def test_disponibilidade_valida(self):
        disponibilidade = DisponibilidadeProfissional(
            profissional=self.profissional,
            dia_semana=0,
            hora_inicio=time(9, 0),
            hora_fim=time(12, 0)
        )

        disponibilidade.full_clean()
        disponibilidade.save()

        self.assertEqual(
            DisponibilidadeProfissional.objects.count(),
            1
        )

    def test_hora_fim_anterior_ao_inicio(self):
        disponibilidade = DisponibilidadeProfissional(
            profissional=self.profissional,
            dia_semana=0,
            hora_inicio=time(12, 0),
            hora_fim=time(9, 0)
        )

        with self.assertRaises(ValidationError) as contexto:
            disponibilidade.full_clean()

        self.assertIn(
            "hora_fim",
            contexto.exception.message_dict
        )

    def test_hora_fim_igual_ao_inicio(self):
        disponibilidade = DisponibilidadeProfissional(
            profissional=self.profissional,
            dia_semana=0,
            hora_inicio=time(9, 0),
            hora_fim=time(9, 0)
        )

        with self.assertRaises(ValidationError) as contexto:
            disponibilidade.full_clean()

        self.assertIn(
            "hora_fim",
            contexto.exception.message_dict
        )
