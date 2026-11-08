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
