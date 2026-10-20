
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date
from django.db.models import ProtectedError
from django.utils import timezone
from .models import Atleta, Responsavel, Usuario



class UsuarioTests(TestCase):

    def setUp(self):
        self.conta = get_user_model().objects.create_user(
            username="teste",
            password="SenhaTeste123!"
        )

    def test_telefone_valido(self):
        usuario = Usuario(
            user=self.conta,
            telefone="21999998888"
        )

        usuario.full_clean()

    def test_telefone_invalido(self):
        usuario = Usuario(
            user=self.conta,
            telefone="219999"
        )

        with self.assertRaises(ValidationError):
            usuario.full_clean()
class AtletaTests(TestCase):

    def setUp(self):
        User = get_user_model()

        conta_responsavel = User.objects.create_user(
            username="responsavel_teste",
            password="SenhaTeste123!"
        )

        perfil_responsavel = Usuario.objects.create(
            user=conta_responsavel
        )

        self.responsavel = Responsavel.objects.create(
            usuario=perfil_responsavel
        )

        self.contador = 0

    def criar_atleta(self, nascimento, responsavel=None):
        self.contador += 1

        conta = get_user_model().objects.create_user(
            username=f"atleta_{self.contador}",
            password="SenhaTeste123!"
        )

        perfil = Usuario.objects.create(user=conta)

        return Atleta(
            usuario=perfil,
            data_de_nascimento=nascimento,
            responsavel=responsavel
        )

    def test_menor_sem_responsavel(self):
        hoje = timezone.localdate()
        nascimento = date(hoje.year - 10, 1, 1)

        atleta = self.criar_atleta(nascimento)

        with self.assertRaises(ValidationError):
            atleta.full_clean()

    def test_menor_com_responsavel(self):
        hoje = timezone.localdate()
        nascimento = date(hoje.year - 10, 1, 1)

        atleta = self.criar_atleta(
            nascimento,
            self.responsavel
        )

        atleta.full_clean()
        atleta.save()

        self.assertEqual(
            atleta.responsavel,
            self.responsavel
        )

    def test_maior_sem_responsavel(self):
        hoje = timezone.localdate()
        nascimento = date(hoje.year - 25, 1, 1)

        atleta = self.criar_atleta(nascimento)

        atleta.full_clean()
        atleta.save()

        self.assertIsNone(atleta.responsavel)

    def test_nascimento_futuro(self):
        hoje = timezone.localdate()
        nascimento = date(hoje.year + 1, 1, 1)

        atleta = self.criar_atleta(
            nascimento,
            self.responsavel
        )

        with self.assertRaises(ValidationError):
            atleta.full_clean()

    def test_responsavel_multiplos_atletas(self):
        hoje = timezone.localdate()
        nascimento = date(hoje.year - 10, 1, 1)

        atleta1 = self.criar_atleta(
            nascimento,
            self.responsavel
        )
        atleta1.full_clean()
        atleta1.save()

        atleta2 = self.criar_atleta(
            nascimento,
            self.responsavel
        )
        atleta2.full_clean()
        atleta2.save()

        self.assertEqual(
            self.responsavel.atletas.count(),
            2
        )

    def test_protecao_exclusao_responsavel(self):
        hoje = timezone.localdate()
        nascimento = date(hoje.year - 10, 1, 1)

        atleta = self.criar_atleta(
            nascimento,
            self.responsavel
        )
        atleta.full_clean()
        atleta.save()

        with self.assertRaises(ProtectedError):
            self.responsavel.delete()

    def test_calculo_idade(self):
        hoje = timezone.localdate()

        atleta = self.criar_atleta(
            date(hoje.year - 20, 1, 1)
        )

        self.assertEqual(atleta.idade, 20)
