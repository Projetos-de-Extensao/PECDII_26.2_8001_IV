
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from .models import(
    Atleta, 
    Responsavel, 
    Usuario,
    Profissional,
    Funcionario
)

## Teste de Usuarios
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

## Teste de Atletas
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

    
    def test_atleta_completa_18_anos_hoje(self):
        hoje = timezone.localdate()

        nascimento = date(
            hoje.year - 18,
            hoje.month,
            hoje.day
        )

        atleta = self.criar_atleta(nascimento)

        self.assertEqual(atleta.idade, 18)

        atleta.full_clean()


    def test_atleta_completa_18_anos_amanha(self):
        hoje = timezone.localdate()
        nascimento = hoje + timedelta(days=1)

        nascimento = nascimento.replace(
            year=nascimento.year - 18
        )

        atleta = self.criar_atleta(nascimento)

        self.assertEqual(atleta.idade, 17)

        with self.assertRaises(ValidationError) as contexto:
            atleta.full_clean()

        self.assertIn(
            "responsavel",
            contexto.exception.message_dict
        )


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

    def teste_usuario_nao_pode_ter_dois_perfis_atleta(self):
        hoje = timezone.localdate()
        nascimento = date(hoje.year - 25, 1, 1)

        atleta1 = self.criar_atleta(nascimento)
        atleta1.full_clean()
        atleta1.save()

        atleta2 = Atleta(
            usuario = atleta1.usuario,
            data_de_nascimento = nascimento
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                atleta2.save()
        self.assertEqual(Atleta.objects.count(), 1)

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

## Teste de Profissional
class ProfissionalTests(TestCase):

    def setUp(self):
        conta = get_user_model().objects.create_user(
            username="profissional_teste",
            password="SenhaTeste123!"
        )

        self.usuario = Usuario.objects.create(user=conta)

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

## Teste de Funcionarios    
class FuncionarioTests(TestCase):

    def setUp(self):
        conta = get_user_model().objects.create_user(
            username="funcionario_teste",
            password="SenhaTeste123!"
        )

        self.usuario = Usuario.objects.create(user=conta)

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

    
