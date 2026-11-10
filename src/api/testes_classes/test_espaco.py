from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# Models necessários para criar e consultar os dados dos testes.
from app.models import Espaco
from usuarios.models import Funcionario, Usuario


# Testes de integração da API REST de espaços.
# Verificam o CRUD completo (criar, listar, detalhar, editar e excluir)
# e se dados inválidos são rejeitados com HTTP 400, sem gerar
# registros indevidos no banco de dados.
class EspacoAPITests(APITestCase):

    def setUp(self):
        # Executado ANTES de cada teste.
        # Prepara os registros necessários em um banco de testes isolado.

        # Cria uma conta de autenticação do Django para o funcionário.
        conta_funcionario = get_user_model().objects.create_user(
            username="funcionario_espaco",
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

        # Cria um espaço já existente, usado nos testes de
        # listagem, detalhe, edição e exclusão.
        self.espaco = Espaco.objects.create(
            nome="Quadra 1",
            tipo="Quadra",
            capacidade=10,
        )

        # Monta o corpo da requisição POST para um novo espaço.
        self.dados = {
            "nome": "Sala de teste",
            "tipo": "Sala",
            "capacidade": 2,
        }

        # Simula autenticação na API usando a conta do funcionário.
        self.client.force_authenticate(user=conta_funcionario)


    def test_criar_espaco_com_sucesso(self):
        # Envia uma requisição HTTP POST com os dados preparados.
        # reverse() encontra a URL pelo nome registrado no router.
        resposta = self.client.post(
            reverse("espaco-list"),
            self.dados,
            format="json",
        )

        # Verifica se a API respondeu com HTTP 201 (Created).
        self.assertEqual(
            resposta.status_code,
            status.HTTP_201_CREATED,
            resposta.data,
        )

        # Verifica se o espaço foi salvo (o do setUp + o novo).
        self.assertEqual(Espaco.objects.count(), 2)

        # Recupera o espaço criado e confere seus atributos.
        espaco = Espaco.objects.get(pk=resposta.data["id"])
        self.assertEqual(espaco.nome, "Sala de teste")
        self.assertEqual(espaco.tipo, "Sala")
        self.assertEqual(espaco.capacidade, 2)


    def test_listar_espacos(self):
        # Cria mais um espaço para a listagem ter dois itens.
        Espaco.objects.create(nome="Sala 2", tipo="Sala", capacidade=4)

        resposta = self.client.get(reverse("espaco-list"))

        # Verifica se a listagem retornou HTTP 200.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        # Confirma que os dois espaços aparecem na resposta.
        nomes = [item["nome"] for item in resposta.data]
        self.assertEqual(len(nomes), 2)
        self.assertIn("Quadra 1", nomes)
        self.assertIn("Sala 2", nomes)


    def test_detalhar_espaco(self):
        resposta = self.client.get(
            reverse("espaco-detail", args=[self.espaco.id])
        )

        # Verifica se o detalhe retornou HTTP 200.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        # Confirma que os dados retornados são os do espaço consultado.
        self.assertEqual(resposta.data["id"], self.espaco.id)
        self.assertEqual(resposta.data["nome"], "Quadra 1")
        self.assertEqual(resposta.data["capacidade"], 10)


    def test_detalhar_espaco_inexistente(self):
        # Consulta um espaço com ID inexistente.
        resposta = self.client.get(
            reverse("espaco-detail", args=[999999])
        )

        # O endpoint deve retornar HTTP 404 (Not Found).
        self.assertEqual(
            resposta.status_code,
            status.HTTP_404_NOT_FOUND,
        )


    def test_atualizar_espaco_com_sucesso(self):
        # PATCH altera apenas os campos enviados.
        resposta = self.client.patch(
            reverse("espaco-detail", args=[self.espaco.id]),
            {"nome": "Quadra Principal", "capacidade": 20},
            format="json",
        )

        # Verifica se a atualização retornou HTTP 200.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        # Consulta novamente o registro no banco de testes.
        self.espaco.refresh_from_db()

        # Confirma que os campos enviados foram alterados.
        self.assertEqual(self.espaco.nome, "Quadra Principal")
        self.assertEqual(self.espaco.capacidade, 20)

        # Confirma que o campo não enviado foi preservado.
        self.assertEqual(self.espaco.tipo, "Quadra")


    def test_excluir_espaco_com_sucesso(self):
        resposta = self.client.delete(
            reverse("espaco-detail", args=[self.espaco.id])
        )

        # Verifica se a exclusão retornou HTTP 204 (No Content).
        self.assertEqual(
            resposta.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        # Confirma que o espaço foi removido do banco.
        self.assertFalse(
            Espaco.objects.filter(pk=self.espaco.id).exists()
        )


    def test_rejeitar_espaco_sem_nome(self):
        # Remove um campo obrigatório dos dados válidos.
        dados = self.dados.copy()
        del dados["nome"]

        resposta = self.client.post(
            reverse("espaco-list"),
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

        # Confirma que nada foi salvo (continua só o espaço do setUp).
        self.assertEqual(Espaco.objects.count(), 1)


    def test_rejeitar_espaco_com_capacidade_negativa(self):
        dados = self.dados.copy()
        dados["capacidade"] = -1

        resposta = self.client.post(
            reverse("espaco-list"),
            dados,
            format="json",
        )

        # capacidade é um PositiveIntegerField: valores negativos
        # devem ser rejeitados.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            resposta.data,
        )
        self.assertIn("capacidade", resposta.data)

        # Confirma que o espaço inválido não foi salvo.
        self.assertEqual(Espaco.objects.count(), 1)


    def test_listar_espacos_ordenados_por_nome(self):
        # O ViewSet usa order_by("nome"), então a API deve devolver
        # os espaços em ordem alfabética, e não na ordem de criação.
        Espaco.objects.create(nome="Sala 2", tipo="Sala", capacidade=4)
        Espaco.objects.create(nome="Academia", tipo="Sala", capacidade=15)

        resposta = self.client.get(reverse("espaco-list"))

        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        nomes = [item["nome"] for item in resposta.data]
        self.assertEqual(nomes, ["Academia", "Quadra 1", "Sala 2"])


    def test_rejeitar_acesso_sem_autenticacao(self):
        # Remove a autenticação simulada no setUp().
        self.client.force_authenticate(user=None)

        # O settings.py exige IsAuthenticated em toda a API.
        resposta = self.client.get(reverse("espaco-list"))

        # Sem login, a API deve negar o acesso. Como a primeira classe
        # de autenticação é a SessionAuthentication, a resposta é 403.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_403_FORBIDDEN,
        )


    def test_rejeitar_criacao_sem_autenticacao(self):
        self.client.force_authenticate(user=None)

        resposta = self.client.post(
            reverse("espaco-list"),
            self.dados,
            format="json",
        )

        self.assertEqual(
            resposta.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        # Confirma que nada foi salvo (continua só o espaço do setUp).
        self.assertEqual(Espaco.objects.count(), 1)


# Testes unitários do model Espaco.
# Verificam as regras do próprio model, sem passar pela API.
class EspacoModelTests(TestCase):

    def setUp(self):
        # Cria um espaço com capacidade para três atletas.
        self.espaco = Espaco.objects.create(
            nome="Sala de teste",
            tipo="Sala",
            capacidade=3,
        )

    def test_comporta_quantidade_dentro_da_capacidade(self):
        # Quantidades de 1 até a capacidade são aceitas.
        self.assertTrue(self.espaco.comporta(1))
        self.assertTrue(self.espaco.comporta(2))

    def test_comporta_quantidade_igual_a_capacidade(self):
        # O limite é inclusivo: lotar o espaço é permitido.
        self.assertTrue(self.espaco.comporta(3))

    def test_nao_comporta_quantidade_acima_da_capacidade(self):
        self.assertFalse(self.espaco.comporta(4))

    def test_nao_comporta_quantidade_zero(self):
        # Um agendamento sem atletas não faz sentido.
        self.assertFalse(self.espaco.comporta(0))

    def test_nao_comporta_quantidade_negativa(self):
        self.assertFalse(self.espaco.comporta(-1))

    def test_str_retorna_nome_e_tipo(self):
        self.assertEqual(str(self.espaco), "Sala de teste - Sala")
