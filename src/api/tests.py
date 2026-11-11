from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

# Models necessários para criar e consultar os dados dos testes.
from agendamentos.models import Agendamento, ParticipacaoAgendamento
from app.models import Espaco
from usuarios.models import (
    Atleta,
    DisponibilidadeProfissional,
    Funcionario,
    Profissional,
    Usuario,
)

# Testes de integração da API REST de agendamentos.
# Verificam se requisições POST com dados válidos criam agendamentos e 
# participações corretamente, retornando HTTP 201.
# Também verificam se conflitos de horário são rejeitados com HTTP 400,
# sem gerar registros indevidos no banco de dados.
# Validam a integração entre Serializer, ViewSet, Service e banco de dados.
class AgendamentoAPITests(APITestCase):

    def setUp(self):
        # Executado ANTES de cada teste.
        # Prepara os registros necessários em um banco de testes isolado.

        # Cria uma conta de autenticação do Django para o profissional.
        conta_profissional = get_user_model().objects.create_user(
            username="profissional_api",
            password="123456",
        )

        # Associa a conta Django ao perfil de usuário do projeto.
        perfil_profissional = Usuario.objects.create(
            user=conta_profissional
        )

        # Cria o profissional que realizará os agendamentos.
        self.profissional = Profissional.objects.create(
            usuario=perfil_profissional,
            especialidade="Fisioterapia",
        )

        # Cria uma segunda conta Django, desta vez para um funcionário.
        conta_funcionario = get_user_model().objects.create_user(
            username="funcionario_api",
            password="123456",
        )

        perfil_funcionario = Usuario.objects.create(
            user=conta_funcionario
        )

        # Cria o funcionário responsável pelo registro do agendamento.
        self.funcionario = Funcionario.objects.create(
            usuario=perfil_funcionario,
            cargo="Recepcionista",
        )

        # Cria um espaço com capacidade para dois atletas.
        self.espaco = Espaco.objects.create(
            nome="Sala de teste",
            tipo="Sala",
            capacidade=2,
        )

        # Cria um atleta adulto que atende aos requisitos básicos para agendamento.
        self.atleta = Atleta.objects.create(
            nome="Atleta de teste",
            data_de_nascimento=date(2000, 1, 1),
        )

        DisponibilidadeProfissional.objects.create(
            profissional=self.profissional,
            dia_semana=0,
            hora_inicio=time(8, 0),
            hora_fim=time(12, 0),
        )

        hoje = timezone.localdate()

        # Calcula quantos dias faltam até a próxima segunda-feira.
        dias_ate_segunda = (0 - hoje.weekday()) % 7
        segunda = hoje + timedelta(days=dias_ate_segunda)

        # Define um agendamento de segunda-feira, 09:00 às 10:00.
        # make_aware() adiciona informação de fuso horário,
        # necessária para as validações do model Agendamento.
        inicio = timezone.make_aware(
            datetime.combine(segunda, time(9, 0))
        )
        fim = timezone.make_aware(
            datetime.combine(segunda, time(10, 0))
        )

        # Monta o corpo da requisição POST.
        # Os IDs serão convertidos em objetos Django pelo serializer.
        self.dados = {
            "profissional": self.profissional.id,
            "espaco": self.espaco.id,
            "atletas": [self.atleta.id],
            "registrado_por": self.funcionario.id,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "modalidade": "individual",
            "limite_participantes": 1,
        }

        # Simula autenticação na API usando a conta do funcionário.
        # Não precisa realizar login com senha neste teste.
        self.client.force_authenticate(user=conta_funcionario)


    def test_criar_agendamento_com_sucesso(self):
        # Envia uma requisição HTTP POST com os dados preparados.
        # reverse() encontra a URL pelo nome registrado no router.
        # format="json" envia os dados como JSON.
        resposta = self.client.post(
            reverse("agendamento-list"),
            self.dados,
            format="json",
        )

        # Verifica se a API respondeu com HTTP 201 (Created).
        # resposta.data será exibido se a comparação falhar,
        # ajudando a identificar o motivo do erro.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_201_CREATED,
            resposta.data,
        )

        # Verifica se exatamente um agendamento foi criado no banco.
        # Equivalente conceitual: SELECT COUNT(*) FROM agendamento;
        self.assertEqual(Agendamento.objects.count(), 1)

        # Recupera o agendamento criado para verificar seus atributos.
        agendamento = Agendamento.objects.get()

        # Confirma que o profissional e o espaço foram salvos corretamente.
        self.assertEqual(agendamento.profissional, self.profissional)
        self.assertEqual(agendamento.espaco, self.espaco)

        # Confirma que o novo agendamento está ativo.
        self.assertEqual(agendamento.situacao, "agendado")

        # Recupera a relação entre o atleta e o agendamento criado.
        participacao = ParticipacaoAgendamento.objects.get(
            agendamento=agendamento
        )

        # Confirma que o atleta correto foi inscrito.
        self.assertEqual(participacao.atleta, self.atleta)

        # Confirma que a participação foi criada como "confirmada".
        self.assertEqual(participacao.situacao, "confirmada")


    def test_rejeitar_agendamento_com_conflito(self):
        # Obtém a URL de criação de agendamentos.
        url = reverse("agendamento-list")

        # Cria o primeiro agendamento.
        primeira_resposta = self.client.post(
            url,
            self.dados,
            format="json",
        )

        # O primeiro agendamento deve ser aceito.
        self.assertEqual(
            primeira_resposta.status_code,
            status.HTTP_201_CREATED,
            primeira_resposta.data,
        )

        # Tenta criar outro agendamento com os mesmos dados:
        # mesmo profissional, mesmo horário, mesmo espaço e atleta.
        segunda_resposta = self.client.post(
            url,
            self.dados,
            format="json",
        )

        # A segunda requisição deve ser rejeitada com HTTP 400.
        # Isso verifica se a API está respeitando as validações
        # de conflito implementadas em agendamentos/services.py.
        self.assertEqual(
            segunda_resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            segunda_resposta.data,
        )

        # Confirma que a resposta contém um erro relacionado
        # ao profissional, que já está ocupado naquele horário.
        self.assertIn("profissional", segunda_resposta.data)

        # Confirma que o agendamento inválido não foi salvo.
        # A quantidade no banco deve continuar sendo exatamente 1.
        self.assertEqual(Agendamento.objects.count(), 1)

        
    def test_cancelar_agendamento_com_sucesso(self):
        # Cria um agendamento válido por meio da própria API.
        resposta_criacao = self.client.post(
            reverse("agendamento-list"),
            self.dados,
            format="json",
        )

        # Confirma que o agendamento inicial foi criado.
        self.assertEqual(
            resposta_criacao.status_code,
            status.HTTP_201_CREATED,
            resposta_criacao.data,
        )

        # Recupera o ID do agendamento retornado pela API.
        agendamento_id = resposta_criacao.data["id"]

        # Solicita o cancelamento, informando seu motivo.
        resposta = self.client.post(
            reverse("agendamento-cancelar", args=[agendamento_id]),
            {"motivo": "Atleta não poderá comparecer."},
            format="json",
        )

        # Verifica se o cancelamento retornou HTTP 200.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        # Consulta novamente os registros no banco de testes.
        agendamento = Agendamento.objects.get(pk=agendamento_id)
        participacao = ParticipacaoAgendamento.objects.get(
            agendamento=agendamento
        )

        # Confirma que o agendamento foi cancelado.
        self.assertEqual(agendamento.situacao, "cancelado")

        # Confirma que o motivo foi registrado corretamente.
        self.assertEqual(
            agendamento.motivo_cancelamento,
            "Atleta não poderá comparecer.",
        )

        # O cancelamento do agendamento inteiro também deve
        # cancelar as participações que estavam confirmadas.
        self.assertEqual(participacao.situacao, "cancelada")

        # Confirma que a API devolveu o estado atualizado.
        self.assertEqual(resposta.data["situacao"], "cancelado")


    def test_cancelar_agendamento_inexistente(self):
        # Tenta cancelar um agendamento com ID inexistente.
        resposta = self.client.post(
            reverse("agendamento-cancelar", args=[999999]),
            {"motivo": "Cancelamento de teste"},
            format="json",
        )

        # O endpoint deve retornar HTTP 404 (Not Found).
        self.assertEqual(
            resposta.status_code,
            status.HTTP_404_NOT_FOUND,
        )


    def test_nao_cancelar_agendamento_realizado(self):
        # Cria um agendamento válido pela API.
        resposta_criacao = self.client.post(
            reverse("agendamento-list"),
            self.dados,
            format="json",
        )

        self.assertEqual(
            resposta_criacao.status_code,
            status.HTTP_201_CREATED,
            resposta_criacao.data,
        )

        # Simula um agendamento que já foi realizado.
        # Alteramos o registro diretamente porque ainda não temos
        # um endpoint para marcar um agendamento como realizado.
        agendamento = Agendamento.objects.get(
            pk=resposta_criacao.data["id"]
        )
        agendamento.situacao = "realizado"
        agendamento.save(update_fields=["situacao"])

        # Tenta cancelar um agendamento já realizado.
        resposta = self.client.post(
            reverse("agendamento-cancelar", args=[agendamento.id]),
            {"motivo": "Tentativa de cancelamento"},
            format="json",
        )

        # A regra de negócio deve impedir a operação.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            resposta.data,
        )

        # Confirma que a resposta identifica o problema.
        self.assertIn("situacao", resposta.data)

        # Verifica que o agendamento continua realizado.
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.situacao, "realizado")

    
    def _criar_atividade_grupo(self):
        # Copia os dados válidos definidos no setUp(),
        # evitando modificar os dados utilizados pelos outros testes.
        dados_grupo = self.dados.copy()

        # Configura a atividade como grupo, permitindo até dois atletas.
        # O espaço criado no setUp() também possui capacidade para dois.
        dados_grupo["modalidade"] = "grupo"
        dados_grupo["limite_participantes"] = 2

        # Cria a atividade por meio do endpoint de agendamentos.
        resposta = self.client.post(
            reverse("agendamento-list"),
            dados_grupo,
            format="json",
        )

        # Verifica se a preparação do cenário foi bem-sucedida.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_201_CREATED,
            resposta.data,
        )

        # Retorna o ID da atividade criada para ser utilizado nos testes.
        return resposta.data["id"]

    
    def test_inscrever_atleta_em_grupo_com_sucesso(self):
        # Cria uma atividade em grupo com um atleta já inscrito.
        agendamento_id = self._criar_atividade_grupo()

        # Cadastra outro atleta para participar da atividade.
        novo_atleta = Atleta.objects.create(
            nome="Segundo atleta",
            data_de_nascimento=date(2000, 1, 1),
        )

        # Solicita a inscrição do novo atleta pela API.
        resposta = self.client.post(
            reverse("agendamento-inscrever", args=[agendamento_id]),
            {
                "atleta": novo_atleta.id,
                "experimental": False,
                "registrado_por": self.funcionario.id,
            },
            format="json",
        )

        # Verifica se a API retornou HTTP 201 (Created).
        self.assertEqual(
            resposta.status_code,
            status.HTTP_201_CREATED,
            resposta.data,
        )

        # Confirma que a participação foi salva no banco.
        participacao = ParticipacaoAgendamento.objects.get(
            agendamento_id=agendamento_id,
            atleta=novo_atleta,
        )

        # Verifica os dados da participação registrada.
        self.assertEqual(participacao.situacao, "confirmada")
        self.assertEqual(participacao.tipo, "regular")

        # Confirma que a atividade agora possui dois participantes.
        self.assertEqual(
            ParticipacaoAgendamento.objects.filter(
                agendamento_id=agendamento_id
            ).count(),
            2,
        )

        # Verifica se a resposta identifica o atleta inscrito.
        self.assertEqual(resposta.data["atleta"], novo_atleta.id)

    
    def test_rejeitar_inscricao_duplicada(self):
        # Cria uma atividade em grupo.
        agendamento_id = self._criar_atividade_grupo()

        # O atleta do setUp() já foi inscrito na criação da atividade.
        # Tentamos inscrevê-lo novamente.
        resposta = self.client.post(
            reverse("agendamento-inscrever", args=[agendamento_id]),
            {
                "atleta": self.atleta.id,
                "experimental": False,
                "registrado_por": self.funcionario.id,
            },
            format="json",
        )

        # A API deve rejeitar a inscrição duplicada.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            resposta.data,
        )

        # Verifica se o erro está associado à validação de atletas.
        self.assertIn("atletas", resposta.data)

        # Confirma que não foi criada outra participação.
        self.assertEqual(
            ParticipacaoAgendamento.objects.filter(
                agendamento_id=agendamento_id
            ).count(),
            1,
        )
    
    def test_rejeitar_inscricao_em_grupo_lotado(self):
        # Cria uma atividade com limite de dois participantes.
        # O primeiro atleta já está inscrito.
        agendamento_id = self._criar_atividade_grupo()

        # Cadastra um segundo e um terceiro atleta.
        segundo_atleta = Atleta.objects.create(
            nome="Segundo atleta",
            data_de_nascimento=date(2000, 1, 1),
        )

        terceiro_atleta = Atleta.objects.create(
            nome="Terceiro atleta",
            data_de_nascimento=date(2000, 1, 1),
        )

        url = reverse(
            "agendamento-inscrever",
            args=[agendamento_id],
        )

        # Inscreve o segundo atleta, preenchendo a última vaga.
        primeira_resposta = self.client.post(
            url,
            {"atleta": segundo_atleta.id},
            format="json",
        )

        self.assertEqual(
            primeira_resposta.status_code,
            status.HTTP_201_CREATED,
            primeira_resposta.data,
        )

        # Tenta inscrever o terceiro atleta na atividade lotada.
        segunda_resposta = self.client.post(
            url,
            {"atleta": terceiro_atleta.id},
            format="json",
        )

        # O service deve rejeitar a inscrição por falta de vagas.
        self.assertEqual(
            segunda_resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            segunda_resposta.data,
        )

        # Verifica se o erro está relacionado ao agendamento.
        self.assertIn("agendamento", segunda_resposta.data)

        # Confirma que apenas duas participações foram registradas.
        self.assertEqual(
            ParticipacaoAgendamento.objects.filter(
                agendamento_id=agendamento_id
            ).count(),
            2,
        )

        # Confirma que o terceiro atleta não foi inscrito.
        self.assertFalse(
            ParticipacaoAgendamento.objects.filter(
                agendamento_id=agendamento_id,
                atleta=terceiro_atleta,
            ).exists()
        )

        
    def test_cancelar_participacao_sem_cancelar_agendamento(self):
        # Cria uma atividade em grupo com um atleta inscrito.
        agendamento_id = self._criar_atividade_grupo()

        # Cadastra um segundo atleta.
        segundo_atleta = Atleta.objects.create(
            nome="Segundo atleta",
            data_de_nascimento=date(2000, 1, 1),
        )

        # Inscreve o segundo atleta na atividade pela API.
        resposta_inscricao = self.client.post(
            reverse("agendamento-inscrever", args=[agendamento_id]),
            {
                "atleta": segundo_atleta.id,
                "registrado_por": self.funcionario.id,
            },
            format="json",
        )

        # Confirma que a inscrição foi realizada.
        self.assertEqual(
            resposta_inscricao.status_code,
            status.HTTP_201_CREATED,
            resposta_inscricao.data,
        )

        # Busca a participação do segundo atleta no banco.
        participacao = ParticipacaoAgendamento.objects.get(
            agendamento_id=agendamento_id,
            atleta=segundo_atleta,
        )

        # Solicita o cancelamento dessa participação pela API.
        resposta = self.client.post(
            reverse(
                "agendamento-cancelar-participacao",
                kwargs={
                    "pk": agendamento_id,
                    "participacao_id": participacao.id,
                },
            ),
            {"motivo": "Desistência do atleta."},
            format="json",
        )

        # Verifica se o endpoint retornou HTTP 200.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        # Atualiza os objetos com os dados persistidos no banco.
        participacao.refresh_from_db()
        agendamento = Agendamento.objects.get(pk=agendamento_id)

        # Confirma que a participação foi cancelada.
        self.assertEqual(participacao.situacao, "cancelada")
        self.assertEqual(
            participacao.motivo_cancelamento,
            "Desistência do atleta.",
        )
        self.assertIsNotNone(participacao.cancelado_em)

        # O agendamento deve continuar ativo.
        self.assertEqual(agendamento.situacao, "agendado")

        # O primeiro atleta deve permanecer inscrito.
        primeira_participacao = ParticipacaoAgendamento.objects.get(
            agendamento_id=agendamento_id,
            atleta=self.atleta,
        )
        self.assertEqual(
            primeira_participacao.situacao,
            "confirmada",
        )

        # Confirma que a resposta representa o agendamento ativo.
        self.assertEqual(resposta.data["situacao"], "agendado")

    
    def test_cancelar_ultima_participacao(self):
        # Cria uma atividade em grupo com apenas um atleta inscrito.
        agendamento_id = self._criar_atividade_grupo()

        # Recupera a única participação existente.
        participacao = ParticipacaoAgendamento.objects.get(
            agendamento_id=agendamento_id,
            atleta=self.atleta,
        )

        # Solicita o cancelamento dessa participação.
        resposta = self.client.post(
            reverse(
                "agendamento-cancelar-participacao",
                kwargs={
                    "pk": agendamento_id,
                    "participacao_id": participacao.id,
                },
            ),
            {"motivo": "Atleta desistiu da atividade."},
            format="json",
        )

        # Confirma que a operação retornou HTTP 200.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_200_OK,
            resposta.data,
        )

        # Consulta o estado atualizado no banco de testes.
        participacao.refresh_from_db()
        agendamento = Agendamento.objects.get(pk=agendamento_id)

        # Verifica se a participação foi cancelada.
        self.assertEqual(participacao.situacao, "cancelada")

        # Como não restam participantes ativos,
        # o próprio agendamento também deve ser cancelado.
        self.assertEqual(agendamento.situacao, "cancelado")

        # Confirma que o motivo foi registrado no agendamento.
        self.assertEqual(
            agendamento.motivo_cancelamento,
            "Atleta desistiu da atividade.",
        )

        # Confirma que a resposta contém a situação atualizada.
        self.assertEqual(resposta.data["situacao"], "cancelado")


    
    def test_rejeitar_cancelamento_de_participacao_presente(self):
        # Cria uma atividade em grupo com um atleta inscrito.
        agendamento_id = self._criar_atividade_grupo()

        # Busca a participação que será utilizada no teste.
        participacao = ParticipacaoAgendamento.objects.get(
            agendamento_id=agendamento_id,
            atleta=self.atleta,
        )

        # Simula uma participação com presença já registrada.
        participacao.situacao = "presente"
        participacao.save(update_fields=["situacao"])

        # Tenta cancelar a participação pela API.
        resposta = self.client.post(
            reverse(
                "agendamento-cancelar-participacao",
                kwargs={
                    "pk": agendamento_id,
                    "participacao_id": participacao.id,
                },
            ),
            {"motivo": "Tentativa de cancelamento."},
            format="json",
        )

        # A regra de negócio deve rejeitar a operação.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_400_BAD_REQUEST,
            resposta.data,
        )

        # Confirma que o erro está associado à situação.
        self.assertIn("situacao", resposta.data)

        # Verifica que a participação não foi alterada.
        participacao.refresh_from_db()
        self.assertEqual(participacao.situacao, "presente")

        # Confirma que o agendamento também não foi cancelado.
        agendamento = Agendamento.objects.get(pk=agendamento_id)
        self.assertEqual(agendamento.situacao, "agendado")


    
    def test_cancelar_participacao_inexistente(self):
        # Cria uma atividade em grupo válida.
        agendamento_id = self._criar_atividade_grupo()

        # Tenta cancelar uma participação com ID inexistente.
        resposta = self.client.post(
            reverse(
                "agendamento-cancelar-participacao",
                kwargs={
                    "pk": agendamento_id,
                    "participacao_id": 999999,
                },
            ),
            {"motivo": "Cancelamento de teste."},
            format="json",
        )

        # A API deve informar que a participação não foi encontrada.
        self.assertEqual(
            resposta.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        # Nenhuma participação existente deve ser alterada.
        participacao = ParticipacaoAgendamento.objects.get(
            agendamento_id=agendamento_id,
            atleta=self.atleta,
        )
        self.assertEqual(participacao.situacao, "confirmada")


# ======================================================================
# ATLETA
# ======================================================================


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


# ======================================================================
# ESPAÇO
# ======================================================================


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


# ======================================================================
# EQUIPAMENTO
# ======================================================================


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


# ======================================================================
# RECURSOS NO AGENDAMENTO
# ======================================================================


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