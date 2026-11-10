from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

# Models necessários para criar e consultar os dados dos testes.
from usuarios.models import Atleta, Funcionario, Responsavel, Usuario


def _nascido_ha_anos(anos):
    # Retorna uma data de nascimento que garante a idade informada hoje.
    # Usa dias (365 por ano + dias bissextos + 1 de folga) em vez de
    # replace(year=...), para não quebrar em 29 de fevereiro.
    return timezone.localdate() - timedelta(
        days=anos * 365 + anos // 4 + 1
    )


def _criar_responsavel(username="responsavel_teste"):
    # Cria a cadeia completa: conta Django -> Usuario -> Responsavel.
    conta = get_user_model().objects.create_user(
        username=username,
        password="123456",
    )
    perfil = Usuario.objects.create(user=conta)
    return Responsavel.objects.create(usuario=perfil)


# Testes de integração da API REST de atletas.
# Verificam o CRUD completo (criar, listar, detalhar, editar e excluir)
# e se dados inválidos são rejeitados com HTTP 400, sem gerar
# registros indevidos no banco de dados.
class AtletaAPITests(APITestCase):

    def setUp(self):
        # Executado ANTES de cada teste.
        # Prepara os registros necessários em um banco de testes isolado.

        # Cria uma conta de autenticação do Django para o funcionário.
        conta_funcionario = get_user_model().objects.create_user(
            username="funcionario_atleta",
            password="123456",
        )

        # Associa a conta Django ao perfil de usuário do projeto.
        perfil_funcionario = Usuario.objects.create(
            user=conta_funcionario
        )

        # Cria o funcionário que fará as requisições.
        self.funcionario = Funcionario.objects.create(
            usuario=perfil_funcionario,
            cargo="Recepcionista",
        )

        # Cria um atleta adulto já existente, usado nos testes de
        # listagem, detalhe, edição e exclusão.
        self.atleta = Atleta.objects.create(
            nome="Atleta de teste",
            data_de_nascimento=_nascido_ha_anos(25),
        )

        # Monta o corpo da requisição POST para um novo atleta.
        self.dados = {
            "nome": "Novo atleta",
            "email": "novo.atleta@exemplo.com",
            "telefone": "11999999999",
            "data_de_nascimento": _nascido_ha_anos(20).isoformat(),
            "objetivos": "Melhorar o condicionamento físico.",
        }

        # Simula autenticação na API usando a conta do funcionário.
        self.client.force_authenticate(user=conta_funcionario)


    def test_criar_atleta_com_sucesso(self):
        # Envia uma requisição HTTP POST com os dados preparados.
        # reverse() encontra a URL pelo nome registrado no router.
        resposta = self.client.post(
            reverse("atleta-list"),
            self.dados,
            format="json",
        )

        # Verifica se a API respondeu com HTTP 201 (Created).
        self.assertEqual(
            resposta.status_code,
            status.HTTP_201_CREATED,
            resposta.data,
        )

        # Verifica se o atleta foi salvo (o do setUp + o novo).
        self.assertEqual(Atleta.objects.count(), 2)

        # Recupera o atleta criado e confere seus atributos.
        atleta = Atleta.objects.get(pk=resposta.data["id"])
        self.assertEqual(atleta.nome, "Novo atleta")
        self.assertEqual(atleta.email, "novo.atleta@exemplo.com")
        self.assertEqual(atleta.telefone, "11999999999")
        self.assertEqual(atleta.idade, 20)

        # Todo atleta novo deve começar ativo.
        self.assertTrue(atleta.ativo)


    def test_criar_atleta_menor_com_responsavel(self):
        # Cria o responsável e envia o menor vinculado a ele.
        responsavel = _criar_responsavel()

        dados = self.dados.copy()
        dados["nome"] = "Atleta menor"
        dados["data_de_nascimento"] = _nascido_ha_anos(10).isoformat()
        dados["responsavel"] = responsavel.id

        resposta = self.client.post(
            reverse("atleta-list"),
            dados,
            format="json",
        )

        # Verifica se a API respondeu com HTTP 201 (Created).
        self.assertEqual(
            resposta.status_code,
            status.HTTP_201_CREATED,
            resposta.data,
        )

        # Confirma que o vínculo com o responsável foi salvo.
        atleta = Atleta.objects.get(pk=resposta.data["id"])
        self.assertEqual(atleta.responsavel, responsavel)


    def test_listar_atletas(self):
        # Cria mais um atleta para a listagem ter dois itens.
        Atleta.objects.create(
            nome="Segundo atleta",
            data_de_nascimento=_nascido_ha_anos(30),
        )

        resposta = self.client.get(reverse("atleta-list"))

        # Verifica se a listagem retornou HTTP 200.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        # Confirma que os dois atletas aparecem na resposta.
        nomes = [item["nome"] for item in resposta.data]
        self.assertEqual(len(nomes), 2)
        self.assertIn("Atleta de teste", nomes)
        self.assertIn("Segundo atleta", nomes)


    def test_detalhar_atleta(self):
        resposta = self.client.get(
            reverse("atleta-detail", args=[self.atleta.id])
        )

        # Verifica se o detalhe retornou HTTP 200.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        # Confirma que os dados retornados são os do atleta consultado.
        self.assertEqual(resposta.data["id"], self.atleta.id)
        self.assertEqual(resposta.data["nome"], "Atleta de teste")


    def test_detalhar_atleta_inexistente(self):
        # Consulta um atleta com ID inexistente.
        resposta = self.client.get(
            reverse("atleta-detail", args=[999999])
        )

        # O endpoint deve retornar HTTP 404 (Not Found).
        self.assertEqual(
            resposta.status_code,
            status.HTTP_404_NOT_FOUND,
        )


    def test_atualizar_atleta_com_sucesso(self):
        # PATCH altera apenas os campos enviados.
        resposta = self.client.patch(
            reverse("atleta-detail", args=[self.atleta.id]),
            {"nome": "Atleta Atualizado", "objetivos": "Ganhar massa."},
            format="json",
        )

        # Verifica se a atualização retornou HTTP 200.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        # Consulta novamente o registro no banco de testes.
        self.atleta.refresh_from_db()

        # Confirma que os campos enviados foram alterados.
        self.assertEqual(self.atleta.nome, "Atleta Atualizado")
        self.assertEqual(self.atleta.objetivos, "Ganhar massa.")

        # Confirma que o campo não enviado foi preservado.
        self.assertEqual(
            self.atleta.data_de_nascimento,
            _nascido_ha_anos(25),
        )


    def test_excluir_atleta_com_sucesso(self):
        resposta = self.client.delete(
            reverse("atleta-detail", args=[self.atleta.id])
        )

        # Verifica se a exclusão retornou HTTP 204 (No Content).
        self.assertEqual(
            resposta.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        # Confirma que o atleta foi removido do banco.
        self.assertFalse(
            Atleta.objects.filter(pk=self.atleta.id).exists()
        )


    def test_rejeitar_atleta_sem_nome(self):
        # Remove um campo obrigatório dos dados válidos.
        dados = self.dados.copy()
        del dados["nome"]

        resposta = self.client.post(
            reverse("atleta-list"),
            dados,
            format="json",
        )

        # A API deve rejeitar a requisição com HTTP 400.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            resposta.data,
        )

        # Confirma que o erro está associado ao campo "nome".
        self.assertIn("nome", resposta.data)

        # Confirma que nada foi salvo (continua só o atleta do setUp).
        self.assertEqual(Atleta.objects.count(), 1)


    def test_rejeitar_atleta_com_email_invalido(self):
        dados = self.dados.copy()
        dados["email"] = "isto-nao-e-um-email"

        resposta = self.client.post(
            reverse("atleta-list"),
            dados,
            format="json",
        )

        # A API deve rejeitar o e-mail mal formatado.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            resposta.data,
        )
        self.assertIn("email", resposta.data)
        self.assertEqual(Atleta.objects.count(), 1)


    def test_rejeitar_atleta_com_data_de_nascimento_futura(self):
        # Esta regra está no clean() do model e é reaproveitada pelo
        # validate() do AtletaSerializer.
        dados = self.dados.copy()
        dados["data_de_nascimento"] = (
            timezone.localdate() + timedelta(days=30)
        ).isoformat()

        resposta = self.client.post(
            reverse("atleta-list"),
            dados,
            format="json",
        )

        self.assertEqual(
            resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            resposta.data,
        )
        self.assertIn("data_de_nascimento", resposta.data)
        self.assertEqual(Atleta.objects.count(), 1)


    def test_rejeitar_atleta_com_telefone_curto(self):
        # Esta regra também está no clean() do model (mínimo de 11 dígitos).
        dados = self.dados.copy()
        dados["telefone"] = "12345"

        resposta = self.client.post(
            reverse("atleta-list"),
            dados,
            format="json",
        )

        self.assertEqual(
            resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            resposta.data,
        )
        self.assertIn("telefone", resposta.data)
        self.assertEqual(Atleta.objects.count(), 1)


    def test_rejeitar_telefone_curto_ao_atualizar(self):
        # No PATCH, o validate() do serializer completa os dados
        # ausentes com os da instância. Aqui só o telefone é enviado.
        resposta = self.client.patch(
            reverse("atleta-detail", args=[self.atleta.id]),
            {"telefone": "12345"},
            format="json",
        )

        self.assertEqual(
            resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            resposta.data,
        )
        self.assertIn("telefone", resposta.data)

        # Confirma que o telefone do atleta não foi alterado.
        self.atleta.refresh_from_db()
        self.assertEqual(self.atleta.telefone, "")


    def test_rejeitar_data_futura_ao_atualizar(self):
        resposta = self.client.patch(
            reverse("atleta-detail", args=[self.atleta.id]),
            {
                "data_de_nascimento": (
                    timezone.localdate() + timedelta(days=30)
                ).isoformat()
            },
            format="json",
        )

        self.assertEqual(
            resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            resposta.data,
        )
        self.assertIn("data_de_nascimento", resposta.data)

        # Confirma que a data original foi preservada.
        self.atleta.refresh_from_db()
        self.assertEqual(
            self.atleta.data_de_nascimento,
            _nascido_ha_anos(25),
        )


    def test_resposta_inclui_idade_calculada(self):
        # "idade" é somente leitura: vem calculada pelo model.
        resposta = self.client.get(
            reverse("atleta-detail", args=[self.atleta.id])
        )

        self.assertEqual(resposta.data["idade"], 25)


    def test_ignorar_idade_enviada_na_criacao(self):
        # Como "idade" é read_only, o valor enviado deve ser ignorado
        # e a idade real, calculada pela data de nascimento.
        dados = self.dados.copy()
        dados["idade"] = 99

        resposta = self.client.post(
            reverse("atleta-list"),
            dados,
            format="json",
        )

        self.assertEqual(
            resposta.status_code,
            status.HTTP_201_CREATED,
            resposta.data,
        )
        self.assertEqual(resposta.data["idade"], 20)


    def test_listar_atletas_ordenados_por_nome(self):
        # O ViewSet usa order_by("nome"), então a API deve devolver
        # os atletas em ordem alfabética, e não na ordem de criação.
        Atleta.objects.create(
            nome="Beto",
            data_de_nascimento=_nascido_ha_anos(30),
        )
        Atleta.objects.create(
            nome="Ana",
            data_de_nascimento=_nascido_ha_anos(30),
        )

        resposta = self.client.get(reverse("atleta-list"))

        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        nomes = [item["nome"] for item in resposta.data]
        self.assertEqual(nomes, ["Ana", "Atleta de teste", "Beto"])


    def test_rejeitar_acesso_sem_autenticacao(self):
        # Remove a autenticação simulada no setUp().
        self.client.force_authenticate(user=None)

        # O settings.py exige IsAuthenticated em toda a API.
        resposta = self.client.get(reverse("atleta-list"))

        # Sem login, a API deve negar o acesso. Como a primeira classe
        # de autenticação é a SessionAuthentication, a resposta é 403.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_403_FORBIDDEN,
        )


    def test_rejeitar_criacao_sem_autenticacao(self):
        self.client.force_authenticate(user=None)

        resposta = self.client.post(
            reverse("atleta-list"),
            self.dados,
            format="json",
        )

        self.assertEqual(
            resposta.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        # Confirma que nada foi salvo (continua só o atleta do setUp).
        self.assertEqual(Atleta.objects.count(), 1)


# Testes unitários do model Atleta.
# Verificam as regras do próprio model, sem passar pela API.
class AtletaModelTests(TestCase):

    def test_idade_calculada_a_partir_da_data_de_nascimento(self):
        atleta = Atleta(
            nome="Atleta adulto",
            data_de_nascimento=_nascido_ha_anos(20),
        )

        self.assertEqual(atleta.idade, 20)

    def test_idade_nula_sem_data_de_nascimento(self):
        atleta = Atleta(nome="Sem data")

        self.assertIsNone(atleta.idade)

    def test_str_retorna_nome(self):
        atleta = Atleta(nome="Maria Souza")

        self.assertEqual(str(atleta), "Maria Souza")

    def test_clean_rejeita_data_de_nascimento_futura(self):
        atleta = Atleta(
            nome="Atleta futuro",
            data_de_nascimento=timezone.localdate() + timedelta(days=1),
        )

        # clean() deve levantar erro associado ao campo da data.
        with self.assertRaises(ValidationError) as contexto:
            atleta.clean()

        self.assertIn("data_de_nascimento", contexto.exception.message_dict)

    def test_clean_rejeita_telefone_com_menos_de_11_digitos(self):
        atleta = Atleta(nome="Atleta", telefone="(11) 9999-999")

        with self.assertRaises(ValidationError) as contexto:
            atleta.clean()

        self.assertIn("telefone", contexto.exception.message_dict)

    def test_clean_aceita_telefone_formatado_com_11_digitos(self):
        # Só os dígitos contam: parênteses, espaços e hífen são ignorados.
        atleta = Atleta(nome="Atleta", telefone="(11) 99999-9999")

        # Não deve levantar exceção.
        atleta.clean()

    def test_validar_para_agendamento_atleta_adulto(self):
        atleta = Atleta.objects.create(
            nome="Atleta adulto",
            data_de_nascimento=_nascido_ha_anos(25),
        )

        # Atleta salvo, com data de nascimento e maior de idade: apto.
        atleta.validar_para_agendamento()

    def test_validar_para_agendamento_exige_atleta_salvo(self):
        # Atleta ainda não salvo no banco (sem pk).
        atleta = Atleta(
            nome="Atleta novo",
            data_de_nascimento=_nascido_ha_anos(25),
        )

        with self.assertRaises(ValidationError) as contexto:
            atleta.validar_para_agendamento()

        self.assertIn("__all__", contexto.exception.message_dict)

    def test_validar_para_agendamento_exige_data_de_nascimento(self):
        atleta = Atleta.objects.create(nome="Sem data")

        with self.assertRaises(ValidationError) as contexto:
            atleta.validar_para_agendamento()

        self.assertIn("data_de_nascimento", contexto.exception.message_dict)

    def test_validar_para_agendamento_menor_sem_responsavel(self):
        atleta = Atleta.objects.create(
            nome="Atleta menor",
            data_de_nascimento=_nascido_ha_anos(10),
        )

        # Menor de 18 anos sem responsável não pode agendar.
        with self.assertRaises(ValidationError) as contexto:
            atleta.validar_para_agendamento()

        self.assertIn("responsavel", contexto.exception.message_dict)

    def test_validar_para_agendamento_menor_com_responsavel(self):
        atleta = Atleta.objects.create(
            nome="Atleta menor",
            data_de_nascimento=_nascido_ha_anos(10),
            responsavel=_criar_responsavel(),
        )

        # Com responsável vinculado, o menor está apto.
        atleta.validar_para_agendamento()

    def test_validar_para_aula_experimental_com_contatos(self):
        atleta = Atleta.objects.create(
            nome="Interessado",
            email="interessado@exemplo.com",
            telefone="11999999999",
            data_de_nascimento=_nascido_ha_anos(25),
        )

        # Com e-mail e telefone informados, está apto à experimental.
        atleta.validar_para_aula_experimental()

    def test_validar_para_aula_experimental_exige_email_e_telefone(self):
        atleta = Atleta.objects.create(
            nome="Interessado",
            data_de_nascimento=_nascido_ha_anos(25),
        )

        with self.assertRaises(ValidationError) as contexto:
            atleta.validar_para_aula_experimental()

        # Os dois campos de contato devem aparecer nos erros.
        erros = contexto.exception.message_dict
        self.assertIn("email", erros)
        self.assertIn("telefone", erros)
