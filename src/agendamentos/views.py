from datetime import date

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from usuarios.models import Atleta, Profissional

from .forms import AgendamentoForm, CancelamentoForm
from .models import Agendamento, ParticipacaoAgendamento
from .services import (
    cancelar_agendamento,
    cancelar_participacao,
    criar_agendamento,
    inscrever_em_atividade_grupo,
    listar_horarios_profissional,
)


def _adicionar_erros_ao_form(form, erro):
    if hasattr(erro, "message_dict"):
        for campo, mensagens in erro.message_dict.items():
            destino = campo if campo in form.fields else None
            for mensagem in mensagens:
                form.add_error(destino, mensagem)
        return

    for mensagem in erro.messages:
        form.add_error(None, mensagem)


@staff_member_required
def lista_agendamentos(request: HttpRequest) -> HttpResponse:
    agendamentos = (
        Agendamento.objects.select_related(
            "profissional__usuario__user",
            "espaco",
            "registrado_por__usuario__user",
        )
        .prefetch_related("participacoes__atleta")
        .annotate(
            inscritos_ativos=Count(
                "participacoes",
                filter=~Q(participacoes__situacao="cancelada"),
                distinct=True,
            )
        )
        .order_by("-inicio", "-id")
    )
    return render(
        request,
        "agendamentos/lista.html",
        {"agendamentos": agendamentos},
    )


@staff_member_required
def novo_agendamento(request: HttpRequest) -> HttpResponse:
    form = AgendamentoForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        dados = form.cleaned_data.copy()
        grupo = dados.pop("agendamento_grupo")
        dados.pop("data")
        novo_atleta = dados.pop("novo_atleta")
        aula_experimental = dados.pop("aula_experimental")
        dados_novo_atleta = {
            "nome": dados.pop("novo_atleta_nome"),
            "email": dados.pop("novo_atleta_email"),
            "telefone": dados.pop("novo_atleta_telefone"),
            "data_de_nascimento": dados.pop(
                "novo_atleta_data_de_nascimento"
            ),
        }

        try:
            with transaction.atomic():
                if novo_atleta:
                    atleta = Atleta(**dados_novo_atleta)
                    atleta.full_clean()
                    atleta.save()
                    dados["atletas"] = [atleta]

                if grupo:
                    participacao = inscrever_em_atividade_grupo(
                        agendamento=grupo,
                        atleta=dados["atletas"][0],
                        experimental=aula_experimental,
                        registrado_por=dados["registrado_por"],
                    )
                    agendamento = participacao.agendamento
                else:
                    atletas_experimentais = (
                        dados["atletas"] if aula_experimental else ()
                    )
                    agendamento = criar_agendamento(
                        **dados,
                        atletas_experimentais=atletas_experimentais,
                    )
        except ValidationError as erro:
            _adicionar_erros_ao_form(form, erro)
        else:
            if novo_atleta:
                messages.success(
                    request,
                    "Interessado cadastrado e aula experimental agendada.",
                )
            elif grupo:
                messages.success(
                    request,
                    "Atleta inscrito na atividade em grupo.",
                )
            else:
                messages.success(request, "Agendamento criado com sucesso.")
            return redirect("agendamentos:detalhe", agendamento.id)

    return render(
        request,
        "agendamentos/formulario.html",
        {"form": form},
    )


@staff_member_required
def horarios_profissional(request: HttpRequest) -> JsonResponse:
    try:
        profissional_id = int(request.GET["profissional"])
        data_selecionada = date.fromisoformat(request.GET["data"])
    except (KeyError, TypeError, ValueError):
        return JsonResponse(
            {"erro": "Informe um profissional e uma data válidos."},
            status=400,
        )

    profissional = get_object_or_404(
        Profissional.objects.filter(ativo=True),
        pk=profissional_id,
    )
    horarios = listar_horarios_profissional(
        profissional=profissional,
        data=data_selecionada,
    )
    return JsonResponse({"horarios": horarios})


@staff_member_required
def detalhe_agendamento(
    request: HttpRequest,
    agendamento_id: int,
) -> HttpResponse:
    agendamento = get_object_or_404(
        Agendamento.objects.select_related(
            "profissional__usuario__user",
            "espaco",
            "registrado_por__usuario__user",
        ).annotate(
            inscritos_ativos=Count(
                "participacoes",
                filter=~Q(participacoes__situacao="cancelada"),
                distinct=True,
            )
        ).prefetch_related(
            "equipamentos",
            Prefetch(
                "participacoes",
                queryset=ParticipacaoAgendamento.objects.select_related(
                    "atleta",
                    "registrado_por__usuario__user",
                ),
            ),
        ),
        pk=agendamento_id,
    )
    return render(
        request,
        "agendamentos/detalhe.html",
        {
            "agendamento": agendamento,
            "cancelamento_form": CancelamentoForm(),
        },
    )


@require_POST
@staff_member_required
def cancelar_agendamento_view(
    request: HttpRequest,
    agendamento_id: int,
) -> HttpResponse:
    agendamento = get_object_or_404(Agendamento, pk=agendamento_id)
    form = CancelamentoForm(request.POST)

    if form.is_valid():
        try:
            cancelar_agendamento(
                agendamento=agendamento,
                motivo=form.cleaned_data["motivo"],
            )
        except ValidationError as erro:
            messages.error(request, " ".join(erro.messages))
        else:
            messages.success(request, "Agendamento inteiro cancelado.")
    else:
        messages.error(request, "Não foi possível validar o cancelamento.")

    return redirect("agendamentos:detalhe", agendamento.id)


@require_POST
@staff_member_required
def cancelar_participacao_view(
    request: HttpRequest,
    participacao_id: int,
) -> HttpResponse:
    participacao = get_object_or_404(
        ParticipacaoAgendamento.objects.select_related("agendamento"),
        pk=participacao_id,
    )
    form = CancelamentoForm(request.POST)

    if form.is_valid():
        try:
            agendamento = cancelar_participacao(
                participacao=participacao,
                motivo=form.cleaned_data["motivo"],
            )
        except ValidationError as erro:
            messages.error(request, " ".join(erro.messages))
        else:
            messages.success(request, "Participação cancelada.")
            return redirect("agendamentos:detalhe", agendamento.id)
    else:
        messages.error(request, "Não foi possível validar o cancelamento.")

    return redirect(
        "agendamentos:detalhe",
        participacao.agendamento_id,
    )
