from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Agendamento


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

    if atletas and sobrepostos.filter(atletas__in=atletas).exists():
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
    agendamento.atletas.set(atletas)
    agendamento.equipamentos.set(equipamentos)
    return agendamento
