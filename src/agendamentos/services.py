from datetime import datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from usuarios.models import (
    JANELAS_HORARIO_PROFISSIONAL,
    horario_alinhado_a_meia_hora,
    periodo_dentro_horario_profissional,
)

from .models import Agendamento, ParticipacaoAgendamento


SITUACOES_PARTICIPACAO_ATIVAS = (
    ParticipacaoAgendamento.Situacao.CONFIRMADA,
    ParticipacaoAgendamento.Situacao.PRESENTE,
    ParticipacaoAgendamento.Situacao.FALTA,
    ParticipacaoAgendamento.Situacao.FALTA_JUSTIFICADA,
)


def _adicionar_erro(erros, campo, mensagem):
    erros.setdefault(campo, []).append(mensagem)


def _validar_atletas(atletas, erros):
    if not atletas:
        _adicionar_erro(
            erros,
            "atletas",
            "Informe pelo menos um atleta.",
        )
        return

    ids_informados = [atleta.pk for atleta in atletas if atleta.pk is not None]
    if len(ids_informados) != len(set(ids_informados)):
        _adicionar_erro(
            erros,
            "atletas",
            "Não repita o mesmo atleta no agendamento.",
        )

    for atleta in atletas:
        if atleta.pk is None:
            _adicionar_erro(
                erros,
                "atletas",
                "Todos os atletas precisam estar salvos antes do agendamento.",
            )
            continue

        if not atleta.ativo:
            _adicionar_erro(
                erros,
                "atletas",
                f"O atleta {atleta} está inativo.",
            )
            continue

        try:
            atleta.validar_para_agendamento()
        except ValidationError as erro:
            for mensagens in erro.message_dict.values():
                for mensagem in mensagens:
                    _adicionar_erro(
                        erros,
                        "atletas",
                        f"{atleta}: {mensagem}",
                    )


def _validar_atletas_experimentais(
    atletas,
    atletas_experimentais,
    registrado_por,
    erros,
):
    ids_atletas = {atleta.pk for atleta in atletas}
    ids_experimentais = {
        atleta.pk for atleta in atletas_experimentais if atleta.pk is not None
    }

    if not ids_experimentais.issubset(ids_atletas):
        _adicionar_erro(
            erros,
            "aula_experimental",
            "Todo aluno experimental precisa participar do agendamento.",
        )
        return

    if atletas_experimentais and (
        registrado_por is None
        or not registrado_por.ativo
        or registrado_por.cargo.strip().casefold() != "recepcionista"
    ):
        _adicionar_erro(
            erros,
            "registrado_por",
            "A aula experimental deve ser registrada por um recepcionista "
            "ativo.",
        )

    for atleta in atletas_experimentais:
        if atleta.pk is None:
            continue

        try:
            atleta.validar_para_aula_experimental()
        except ValidationError as erro:
            for mensagens in erro.message_dict.values():
                for mensagem in mensagens:
                    _adicionar_erro(
                        erros,
                        "aula_experimental",
                        f"{atleta}: {mensagem}",
                    )

        if atleta.participacoes_agendamento.filter(
            tipo=ParticipacaoAgendamento.Tipo.EXPERIMENTAL,
        ).exclude(
            situacao=ParticipacaoAgendamento.Situacao.CANCELADA,
        ).exists():
            _adicionar_erro(
                erros,
                "aula_experimental",
                f"{atleta} já utilizou ou possui uma aula experimental.",
            )


def _validar_modalidade(
    modalidade,
    limite_participantes,
    atletas,
    erros,
):
    if (
        modalidade == Agendamento.Modalidade.INDIVIDUAL
        and len(atletas) != 1
    ):
        _adicionar_erro(
            erros,
            "atletas",
            "Uma atividade individual deve possuir exatamente um atleta.",
        )

    if len(atletas) > limite_participantes:
        _adicionar_erro(
            erros,
            "limite_participantes",
            "O limite não pode ser menor que a quantidade de atletas "
            "já inscritos.",
        )


def _validar_disponibilidade(profissional, inicio, fim, erros):
    inicio_local = timezone.localtime(inicio)
    fim_local = timezone.localtime(fim)

    if not (
        horario_alinhado_a_meia_hora(inicio_local.time())
        and horario_alinhado_a_meia_hora(fim_local.time())
    ):
        _adicionar_erro(
            erros,
            "profissional",
            "Os agendamentos devem usar intervalos de 30 minutos.",
        )
        return

    if not periodo_dentro_horario_profissional(
        inicio_local.time(),
        fim_local.time(),
    ):
        _adicionar_erro(
            erros,
            "profissional",
            "Os agendamentos devem ocorrer entre 07:00 e 12:00 "
            "ou entre 13:00 e 20:00.",
        )
        return

    disponibilidades = profissional.disponibilidades.all()

    if not disponibilidades.exists():
        _adicionar_erro(
            erros,
            "profissional",
            "O profissional não possui horários de disponibilidade "
            "cadastrados.",
        )
        return

    disponivel = disponibilidades.filter(
        dia_semana=inicio_local.weekday(),
        hora_inicio__lte=inicio_local.time(),
        hora_fim__gte=fim_local.time(),
    ).exists()

    if not disponivel:
        _adicionar_erro(
            erros,
            "profissional",
            "O horário está fora da disponibilidade do profissional.",
        )


def _validar_conflitos(
    profissional,
    espaco,
    atletas,
    equipamentos,
    inicio,
    fim,
    limite_participantes,
    erros,
):
    sobrepostos = Agendamento.objects.exclude(
        situacao=Agendamento.Situacao.CANCELADO,
    ).filter(
        inicio__lt=fim,
        fim__gt=inicio,
    )

    if sobrepostos.filter(profissional=profissional).exists():
        _adicionar_erro(
            erros,
            "profissional",
            "O profissional já possui um agendamento nesse horário.",
        )

    vagas_reservadas = (
        sobrepostos.filter(espaco=espaco).aggregate(
            total=Sum("limite_participantes")
        )["total"]
        or 0
    )
    if vagas_reservadas + limite_participantes > espaco.capacidade:
        _adicionar_erro(
            erros,
            "espaco",
            "O espaço escolhido está lotado nesse horário. "
            f"Capacidade: {espaco.capacidade}; vagas já reservadas: "
            f"{vagas_reservadas}; novo limite: {limite_participantes}.",
        )

    if atletas and sobrepostos.filter(
        participacoes__atleta__in=atletas,
        participacoes__situacao__in=SITUACOES_PARTICIPACAO_ATIVAS,
    ).exists():
        _adicionar_erro(
            erros,
            "atletas",
            "Um ou mais atletas já possuem agendamento nesse horário.",
        )

    if equipamentos and sobrepostos.filter(
        equipamentos__in=equipamentos
    ).exists():
        _adicionar_erro(
            erros,
            "equipamentos",
            "Um ou mais equipamentos já estão reservados nesse horário.",
        )


@transaction.atomic
def criar_agendamento(
    *,
    profissional,
    espaco,
    atletas,
    registrado_por,
    inicio,
    fim,
    equipamentos=(),
    observacoes="",
    modalidade=None,
    limite_participantes=None,
    atletas_experimentais=(),
):
    """Valida e cria um agendamento simples ou em grupo."""
    atletas = tuple(atletas)
    atletas_experimentais = tuple(atletas_experimentais)
    equipamentos = tuple(equipamentos)

    ids_atletas = [atleta.pk for atleta in atletas if atleta.pk is not None]
    if ids_atletas:
        list(
            atletas[0].__class__.objects.select_for_update().filter(
                pk__in=ids_atletas
            )
        )

    if profissional.pk is not None:
        profissional = profissional.__class__.objects.select_for_update().get(
            pk=profissional.pk
        )
    if espaco.pk is not None:
        espaco = espaco.__class__.objects.select_for_update().get(pk=espaco.pk)

    if modalidade is None:
        modalidade = (
            Agendamento.Modalidade.GRUPO
            if len(atletas) > 1
            else Agendamento.Modalidade.INDIVIDUAL
        )
    if limite_participantes is None:
        limite_participantes = max(len(atletas), 1)

    agendamento = Agendamento(
        profissional=profissional,
        espaco=espaco,
        registrado_por=registrado_por,
        inicio=inicio,
        fim=fim,
        observacoes=observacoes,
        modalidade=modalidade,
        limite_participantes=limite_participantes,
    )
    agendamento.full_clean()

    erros = {}
    _validar_atletas(atletas, erros)
    _validar_atletas_experimentais(
        atletas,
        atletas_experimentais,
        registrado_por,
        erros,
    )
    _validar_modalidade(
        modalidade,
        limite_participantes,
        atletas,
        erros,
    )
    _validar_disponibilidade(
        profissional,
        inicio,
        fim,
        erros,
    )
    _validar_conflitos(
        profissional,
        espaco,
        atletas,
        equipamentos,
        inicio,
        fim,
        limite_participantes,
        erros,
    )

    if erros:
        raise ValidationError(erros)

    agendamento.save()
    ids_experimentais = {atleta.pk for atleta in atletas_experimentais}
    ParticipacaoAgendamento.objects.bulk_create(
        ParticipacaoAgendamento(
            agendamento=agendamento,
            atleta=atleta,
            registrado_por=registrado_por,
            tipo=(
                ParticipacaoAgendamento.Tipo.EXPERIMENTAL
                if atleta.pk in ids_experimentais
                else ParticipacaoAgendamento.Tipo.REGULAR
            ),
        )
        for atleta in atletas
    )
    agendamento.equipamentos.set(equipamentos)
    return agendamento


@transaction.atomic
def inscrever_em_atividade_grupo(
    *,
    agendamento,
    atleta,
    experimental=False,
    registrado_por=None,
):
    """Inscreve um atleta em uma atividade em grupo que ainda possui vaga."""
    if agendamento.pk is None:
        raise ValidationError({
            "agendamento": "O agendamento precisa estar salvo para inscrição."
        })

    agendamento = (
        Agendamento.objects.select_for_update()
        .select_related("espaco")
        .get(pk=agendamento.pk)
    )
    atleta = atleta.__class__.objects.select_for_update().get(pk=atleta.pk)

    erros = {}
    if agendamento.situacao != Agendamento.Situacao.AGENDADO:
        _adicionar_erro(
            erros,
            "agendamento",
            "Somente atividades agendadas aceitam novas inscrições.",
        )

    if agendamento.modalidade != Agendamento.Modalidade.GRUPO:
        _adicionar_erro(
            erros,
            "agendamento",
            "Somente atividades em grupo aceitam novas inscrições.",
        )

    _validar_atletas((atleta,), erros)
    _validar_atletas_experimentais(
        (atleta,),
        (atleta,) if experimental else (),
        registrado_por,
        erros,
    )

    participacoes = agendamento.participacoes.select_for_update()
    participacao_existente = participacoes.filter(atleta=atleta).first()
    if (
        participacao_existente
        and participacao_existente.situacao
        != ParticipacaoAgendamento.Situacao.CANCELADA
    ):
        _adicionar_erro(
            erros,
            "atletas",
            "O atleta já está inscrito nessa atividade.",
        )

    inscritos = participacoes.filter(
        situacao__in=SITUACOES_PARTICIPACAO_ATIVAS
    ).count()
    if inscritos >= agendamento.limite_participantes:
        _adicionar_erro(
            erros,
            "agendamento",
            "A atividade em grupo está lotada.",
        )

    conflito_atleta = (
        Agendamento.objects.exclude(pk=agendamento.pk)
        .exclude(situacao=Agendamento.Situacao.CANCELADO)
        .filter(
            inicio__lt=agendamento.fim,
            fim__gt=agendamento.inicio,
            participacoes__atleta=atleta,
            participacoes__situacao__in=SITUACOES_PARTICIPACAO_ATIVAS,
        )
        .exists()
    )
    if conflito_atleta:
        _adicionar_erro(
            erros,
            "atletas",
            "O atleta já possui outro agendamento nesse horário.",
        )

    if erros:
        raise ValidationError(erros)

    if participacao_existente:
        participacao_existente.situacao = (
            ParticipacaoAgendamento.Situacao.CONFIRMADA
        )
        participacao_existente.motivo_cancelamento = ""
        participacao_existente.cancelado_em = None
        participacao_existente.registrado_por = registrado_por
        participacao_existente.tipo = (
            ParticipacaoAgendamento.Tipo.EXPERIMENTAL
            if experimental
            else ParticipacaoAgendamento.Tipo.REGULAR
        )
        participacao_existente.save(update_fields=[
            "situacao",
            "motivo_cancelamento",
            "cancelado_em",
            "registrado_por",
            "tipo",
            "atualizado_em",
        ])
        return participacao_existente

    return ParticipacaoAgendamento.objects.create(
        agendamento=agendamento,
        atleta=atleta,
        registrado_por=registrado_por,
        tipo=(
            ParticipacaoAgendamento.Tipo.EXPERIMENTAL
            if experimental
            else ParticipacaoAgendamento.Tipo.REGULAR
        ),
    )


def listar_horarios_profissional(*, profissional, data):
    """Gera blocos de 30 minutos e informa vagas/ocupação de cada um."""
    disponibilidades = profissional.disponibilidades.filter(
        dia_semana=data.weekday()
    ).order_by("hora_inicio", "hora_fim")

    inicio_dia = timezone.make_aware(datetime.combine(data, time.min))
    fim_dia = inicio_dia + timedelta(days=1)
    agendamentos = list(
        Agendamento.objects.exclude(
            situacao=Agendamento.Situacao.CANCELADO
        )
        .filter(
            profissional=profissional,
            inicio__lt=fim_dia,
            fim__gt=inicio_dia,
        )
        .annotate(
            inscritos_ativos=Count(
                "participacoes",
                filter=Q(
                    participacoes__situacao__in=(
                        SITUACOES_PARTICIPACAO_ATIVAS
                    )
                ),
                distinct=True,
            )
        )
    )

    disponibilidades = list(disponibilidades)
    blocos = {}
    duracao = timedelta(minutes=30)
    for inicio_janela, fim_janela in JANELAS_HORARIO_PROFISSIONAL:
        inicio = timezone.make_aware(datetime.combine(data, inicio_janela))
        fim_janela_data = timezone.make_aware(
            datetime.combine(data, fim_janela)
        )

        while inicio + duracao <= fim_janela_data:
            fim = inicio + duracao
            inicio_hora = timezone.localtime(inicio).time()
            fim_hora = timezone.localtime(fim).time()
            coberto_por_disponibilidade = any(
                disponibilidade.hora_inicio <= inicio_hora
                and disponibilidade.hora_fim >= fim_hora
                for disponibilidade in disponibilidades
            )
            if not coberto_por_disponibilidade:
                inicio = fim
                continue

            chave = inicio.isoformat()
            agendamento = next(
                (
                    item
                    for item in agendamentos
                    if item.inicio < fim and item.fim > inicio
                ),
                None,
            )

            bloco = {
                "rotulo": timezone.localtime(inicio).strftime("%H:%M"),
                "inicio": timezone.localtime(inicio).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "fim": timezone.localtime(fim).strftime("%Y-%m-%dT%H:%M"),
                "disponivel": agendamento is None,
                "tipo": "livre" if agendamento is None else "individual",
                "agendamento_id": None,
                "inscritos": None,
                "limite": None,
            }

            if (
                agendamento
                and agendamento.modalidade == Agendamento.Modalidade.GRUPO
            ):
                bloco.update({
                    "disponivel": (
                        agendamento.inscritos_ativos
                        < agendamento.limite_participantes
                    ),
                    "tipo": "grupo",
                    "agendamento_id": agendamento.pk,
                    "inscritos": agendamento.inscritos_ativos,
                    "limite": agendamento.limite_participantes,
                })

            blocos[chave] = bloco
            inicio = fim

    return list(blocos.values())


@transaction.atomic
def cancelar_participacao(*, participacao, motivo=""):
    """Cancela um atleta e encerra o agendamento se ele ficar vazio."""
    if participacao.pk is None:
        raise ValidationError({
            "participacao": "A participação precisa estar salva para cancelar."
        })

    agendamento = Agendamento.objects.select_for_update().get(
        pk=participacao.agendamento_id
    )
    participacao = ParticipacaoAgendamento.objects.select_for_update().get(
        pk=participacao.pk
    )

    if participacao.situacao == ParticipacaoAgendamento.Situacao.CANCELADA:
        return agendamento

    if agendamento.situacao != Agendamento.Situacao.AGENDADO:
        raise ValidationError({
            "situacao": "Somente agendamentos ativos podem ser cancelados."
        })

    if participacao.situacao != ParticipacaoAgendamento.Situacao.CONFIRMADA:
        raise ValidationError({
            "situacao": (
                "Somente uma participação confirmada pode ser cancelada."
            )
        })

    agora = timezone.now()
    participacao.situacao = ParticipacaoAgendamento.Situacao.CANCELADA
    participacao.motivo_cancelamento = motivo
    participacao.cancelado_em = agora
    participacao.save(update_fields=[
        "situacao",
        "motivo_cancelamento",
        "cancelado_em",
        "atualizado_em",
    ])

    possui_outros_participantes = agendamento.participacoes.exclude(
        situacao=ParticipacaoAgendamento.Situacao.CANCELADA
    ).exists()

    if not possui_outros_participantes:
        agendamento.situacao = Agendamento.Situacao.CANCELADO
        agendamento.motivo_cancelamento = (
            motivo or "Todos os participantes cancelaram."
        )
        agendamento.cancelado_em = agora
        agendamento.save(update_fields=[
            "situacao",
            "motivo_cancelamento",
            "cancelado_em",
            "atualizado_em",
        ])

    return agendamento


@transaction.atomic
def cancelar_agendamento(*, agendamento, motivo=""):
    """Cancela o atendimento inteiro e suas participações confirmadas."""
    if agendamento.pk is None:
        raise ValidationError({
            "agendamento": "O agendamento precisa estar salvo para cancelar."
        })

    agendamento = Agendamento.objects.select_for_update().get(
        pk=agendamento.pk
    )

    if agendamento.situacao == Agendamento.Situacao.CANCELADO:
        return agendamento

    if agendamento.situacao != Agendamento.Situacao.AGENDADO:
        raise ValidationError({
            "situacao": "Somente agendamentos ativos podem ser cancelados."
        })

    participacoes = agendamento.participacoes.select_for_update()
    if participacoes.exclude(
        situacao__in=(
            ParticipacaoAgendamento.Situacao.CONFIRMADA,
            ParticipacaoAgendamento.Situacao.CANCELADA,
        )
    ).exists():
        raise ValidationError({
            "situacao": (
                "O agendamento possui presença ou falta registrada e não "
                "pode ser cancelado."
            )
        })

    agora = timezone.now()
    participacoes.filter(
        situacao=ParticipacaoAgendamento.Situacao.CONFIRMADA
    ).update(
        situacao=ParticipacaoAgendamento.Situacao.CANCELADA,
        motivo_cancelamento=motivo,
        cancelado_em=agora,
        atualizado_em=agora,
    )

    agendamento.situacao = Agendamento.Situacao.CANCELADO
    agendamento.motivo_cancelamento = motivo
    agendamento.cancelado_em = agora
    agendamento.save(update_fields=[
        "situacao",
        "motivo_cancelamento",
        "cancelado_em",
        "atualizado_em",
    ])
    return agendamento
