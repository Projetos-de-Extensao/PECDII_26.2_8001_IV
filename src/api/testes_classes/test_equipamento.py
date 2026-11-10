from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# Models necessários para criar e consultar os dados dos testes.
from app.models import Equipamento
from usuarios.models import Funcionario, Usuario


# Testes de integração da API REST de equipamentos.
# Verificam o CRUD completo (criar, listar, detalhar, editar e excluir)
# e se dados inválidos são rejeitados com HTTP 400, sem gerar
# registros indevidos no banco de dados.
class EquipamentoAPITests(APITestCase):

    def setUp(self):
        # Executado ANTES de cada teste.
        # Prepara os registros necessários em um banco de testes isolado.

        # Cria uma conta de autenticação do Django para o funcionário.
        conta_funcionario = get_user_model().objects.create_user(
            username="funcionario_equipamento",
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

        # Cria um equipamento já existente, usado nos testes de
        # listagem, detalhe, edição e exclusão.
        self.equipamento = Equipamento.objects.create(
            nome="Bola de vôlei",
            tipo="Bola",
        )

        # Monta o corpo da requisição POST para um novo equipamento.
        self.dados = {
            "nome": "Colchonete",
            "tipo": "Fisioterapia",
        }

        # Simula autenticação na API usando a conta do funcionário.
        self.client.force_authenticate(user=conta_funcionario)


    def test_criar_equipamento_com_sucesso(self):
        # Envia uma requisição HTTP POST com os dados preparados.
        # reverse() encontra a URL pelo nome registrado no router.
        resposta = self.client.post(
            reverse("equipamento-list"),
            self.dados,
            format="json",
        )

        # Verifica se a API respondeu com HTTP 201 (Created).
        self.assertEqual(
            resposta.status_code,
            status.HTTP_201_CREATED,
            resposta.data,
        )

        # Verifica se o equipamento foi salvo (o do setUp + o novo).
        self.assertEqual(Equipamento.objects.count(), 2)

        # Recupera o equipamento criado e confere seus atributos.
        equipamento = Equipamento.objects.get(pk=resposta.data["id"])
        self.assertEqual(equipamento.nome, "Colchonete")
        self.assertEqual(equipamento.tipo, "Fisioterapia")


    def test_listar_equipamentos(self):
        # Cria mais um equipamento para a listagem ter dois itens.
        Equipamento.objects.create(nome="Rede", tipo="Quadra")

        resposta = self.client.get(reverse("equipamento-list"))

        # Verifica se a listagem retornou HTTP 200.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        # Confirma que os dois equipamentos aparecem na resposta.
        nomes = [item["nome"] for item in resposta.data]
        self.assertEqual(len(nomes), 2)
        self.assertIn("Bola de vôlei", nomes)
        self.assertIn("Rede", nomes)


    def test_detalhar_equipamento(self):
        resposta = self.client.get(
            reverse("equipamento-detail", args=[self.equipamento.id])
        )

        # Verifica se o detalhe retornou HTTP 200.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        # Confirma que os dados retornados são os do equipamento consultado.
        self.assertEqual(resposta.data["id"], self.equipamento.id)
        self.assertEqual(resposta.data["nome"], "Bola de vôlei")
        self.assertEqual(resposta.data["tipo"], "Bola")


    def test_detalhar_equipamento_inexistente(self):
        # Consulta um equipamento com ID inexistente.
        resposta = self.client.get(
            reverse("equipamento-detail", args=[999999])
        )

        # O endpoint deve retornar HTTP 404 (Not Found).
        self.assertEqual(
            resposta.status_code,
            status.HTTP_404_NOT_FOUND,
        )


    def test_atualizar_equipamento_com_sucesso(self):
        # PATCH altera apenas os campos enviados.
        resposta = self.client.patch(
            reverse("equipamento-detail", args=[self.equipamento.id]),
            {"nome": "Bola de basquete"},
            format="json",
        )

        # Verifica se a atualização retornou HTTP 200.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        # Consulta novamente o registro no banco de testes.
        self.equipamento.refresh_from_db()

        # Confirma que o campo enviado foi alterado.
        self.assertEqual(self.equipamento.nome, "Bola de basquete")

        # Confirma que o campo não enviado foi preservado.
        self.assertEqual(self.equipamento.tipo, "Bola")


    def test_excluir_equipamento_com_sucesso(self):
        resposta = self.client.delete(
            reverse("equipamento-detail", args=[self.equipamento.id])
        )

        # Verifica se a exclusão retornou HTTP 204 (No Content).
        self.assertEqual(
            resposta.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        # Confirma que o equipamento foi removido do banco.
        self.assertFalse(
            Equipamento.objects.filter(pk=self.equipamento.id).exists()
        )


    def test_rejeitar_equipamento_sem_nome(self):
        # Remove um campo obrigatório dos dados válidos.
        dados = self.dados.copy()
        del dados["nome"]

        resposta = self.client.post(
            reverse("equipamento-list"),
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

        # Confirma que nada foi salvo (continua só o do setUp).
        self.assertEqual(Equipamento.objects.count(), 1)


    def test_rejeitar_equipamento_sem_tipo(self):
        dados = self.dados.copy()
        del dados["tipo"]

        resposta = self.client.post(
            reverse("equipamento-list"),
            dados,
            format="json",
        )

        # A API deve rejeitar a requisição com HTTP 400.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            resposta.data,
        )

        # Confirma que o erro está associado ao campo "tipo".
        self.assertIn("tipo", resposta.data)
        self.assertEqual(Equipamento.objects.count(), 1)


    def test_listar_equipamentos_ordenados_por_nome(self):
        # O ViewSet usa order_by("nome"), então a API deve devolver
        # os equipamentos em ordem alfabética, e não na ordem de criação.
        Equipamento.objects.create(nome="Rede", tipo="Quadra")
        Equipamento.objects.create(nome="Aro", tipo="Basquete")

        resposta = self.client.get(reverse("equipamento-list"))

        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        nomes = [item["nome"] for item in resposta.data]
        self.assertEqual(nomes, ["Aro", "Bola de vôlei", "Rede"])


    def test_rejeitar_acesso_sem_autenticacao(self):
        # Remove a autenticação simulada no setUp().
        self.client.force_authenticate(user=None)

        # O settings.py exige IsAuthenticated em toda a API.
        resposta = self.client.get(reverse("equipamento-list"))

        # Sem login, a API deve negar o acesso. Como a primeira classe
        # de autenticação é a SessionAuthentication, a resposta é 403.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_403_FORBIDDEN,
        )


    def test_rejeitar_criacao_sem_autenticacao(self):
        self.client.force_authenticate(user=None)

        resposta = self.client.post(
            reverse("equipamento-list"),
            self.dados,
            format="json",
        )

        self.assertEqual(
            resposta.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        # Confirma que nada foi salvo (continua só o do setUp).
        self.assertEqual(Equipamento.objects.count(), 1)


# Testes unitários do model Equipamento.
class EquipamentoModelTests(TestCase):

    def test_str_retorna_nome_e_tipo(self):
        equipamento = Equipamento.objects.create(
            nome="Colchonete",
            tipo="Fisioterapia",
        )

        self.assertEqual(str(equipamento), "Colchonete - Fisioterapia")
