from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Agendamento, ParticipacaoAgendamento


def _adicionar_erro(erros, campo, mensagem):
    erros.setdefault(campo, []).append(mensagem)


def _validar_atletas(atletas, espaco, erros):
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

    if len(atletas) > espaco.capacidade:
        _adicionar_erro(
            erros,
            "atletas",
            "A quantidade de atletas excede a capacidade do espaço.",
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


def _validar_disponibilidade(profissional, inicio, fim, erros):
    inicio_local = timezone.localtime(inicio)
    fim_local = timezone.localtime(fim)

    disponivel = profissional.disponibilidades.filter(
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

    if sobrepostos.filter(espaco=espaco).exists():
        _adicionar_erro(
            erros,
            "espaco",
            "O espaço já possui um agendamento nesse horário.",
        )

    situacoes_ativas = (
        ParticipacaoAgendamento.Situacao.CONFIRMADA,
        ParticipacaoAgendamento.Situacao.PRESENTE,
        ParticipacaoAgendamento.Situacao.FALTA,
        ParticipacaoAgendamento.Situacao.FALTA_JUSTIFICADA,
    )

    if atletas and sobrepostos.filter(
        participacoes__atleta__in=atletas,
        participacoes__situacao__in=situacoes_ativas,
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
):
    """Valida e cria um agendamento simples ou em grupo."""
    atletas = tuple(atletas)
    equipamentos = tuple(equipamentos)

    agendamento = Agendamento(
        profissional=profissional,
        espaco=espaco,
        registrado_por=registrado_por,
        inicio=inicio,
        fim=fim,
        observacoes=observacoes,
    )
    agendamento.full_clean()

    erros = {}
    _validar_atletas(atletas, espaco, erros)
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
        erros,
    )

    if erros:
        raise ValidationError(erros)

    agendamento.save()
    ParticipacaoAgendamento.objects.bulk_create(
        ParticipacaoAgendamento(
            agendamento=agendamento,
            atleta=atleta,
        )
        for atleta in atletas
    )
    agendamento.equipamentos.set(equipamentos)
    return agendamento


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
