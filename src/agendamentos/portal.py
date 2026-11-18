from datetime import datetime, timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from usuarios.models import Atleta, Profissional

from .models import Agendamento, Espaco, ParticipacaoAgendamento, SolicitacaoReserva
from .services import criar_agendamento, inscrever_em_atividade_grupo, listar_horarios_profissional


DIAS_MAXIMOS_RESERVA = 45


def acesso_atleta(user):
    return Q(usuario__user=user) | Q(responsavel__usuario__user=user)


class ReservaPortalForm(forms.Form):
    atleta = forms.ModelChoiceField(label="Atleta", queryset=Atleta.objects.none())
    profissional = forms.ModelChoiceField(
        label="Profissional", queryset=Profissional.objects.filter(ativo=True)
    )
    data = forms.DateField(
        label="Data",
        input_formats=["%d/%m/%Y", "%Y-%m-%d"],
        widget=forms.DateInput(
            format="%d/%m/%Y",
            attrs={"placeholder": "dd/mm/aaaa", "inputmode": "numeric", "data-calendario": "agendamento"},
        ),
        error_messages={"invalid": "Informe uma data válida no formato dd/mm/aaaa."},
    )
    espaco = forms.ModelChoiceField(
        label="Espaço para aula individual",
        queryset=Espaco.objects.order_by("nome"),
        required=False,
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["atleta"].queryset = Atleta.objects.filter(acesso_atleta(user), ativo=True)
        self.data_minima = timezone.localdate()
        self.data_maxima = self.data_minima + timedelta(days=DIAS_MAXIMOS_RESERVA)
        self.fields["data"].widget.attrs.update({
            "data-minima": self.data_minima.strftime("%d/%m/%Y"),
            "data-maxima": self.data_maxima.strftime("%d/%m/%Y"),
            "aria-describedby": "reserva-intervalo-data",
        })

    def clean_data(self):
        data = self.cleaned_data["data"]
        if data < self.data_minima:
            raise ValidationError("Escolha a data de hoje ou uma data futura.")
        if data > self.data_maxima:
            raise ValidationError(
                "Você pode agendar com até %(dias)s dias de antecedência.",
                params={"dias": DIAS_MAXIMOS_RESERVA},
            )
        return data


def opcoes_de_reserva(profissional, data):
    agora = timezone.now()
    opcoes = {}
    for bloco in listar_horarios_profissional(profissional=profissional, data=data):
        if bloco["disponivel"] and bloco["tipo"] == "livre":
            inicio = timezone.make_aware(datetime.fromisoformat(bloco["inicio"]))
            fim = timezone.make_aware(datetime.fromisoformat(bloco["fim"]))
            if inicio > agora:
                opcoes[f"individual-{bloco['inicio']}"] = {
                    "rotulo": f"{inicio:%H:%M}–{fim:%H:%M} · Individual",
                    "inicio": inicio,
                    "fim": fim,
                }
    grupos = Agendamento.objects.filter(
        profissional=profissional,
        inicio__date=data,
        inicio__gt=agora,
        modalidade=Agendamento.Modalidade.GRUPO,
        situacao=Agendamento.Situacao.AGENDADO,
    ).select_related("espaco").order_by("inicio")

    for grupo in grupos:
        inicio = timezone.localtime(grupo.inicio)
        fim = timezone.localtime(grupo.fim)
        opcoes[f"grupo-{grupo.pk}"] = {
            "rotulo": f"{inicio:%H:%M}–{fim:%H:%M} · Grupo · {grupo.espaco}",
            "inicio": inicio,
            "grupo": grupo,
        }
    return dict(sorted(opcoes.items(), key=lambda item: item[1]["inicio"]))


@login_required
def reservar_aula(request):
    form = ReservaPortalForm(
        request.POST if request.method == "POST" else None, user=request.user
    )
    opcoes = {}
    if form.is_valid():
        dados = form.cleaned_data
        opcoes = opcoes_de_reserva(dados["profissional"], dados["data"])
        if request.POST.get("acao") == "reservar":
            escolha = opcoes.get(request.POST.get("horario"))
            try:
                if escolha is None:
                    raise ValidationError("Escolha um horário disponível.")
                atleta = dados["atleta"]
                atleta.validar_para_agendamento()
                grupo = escolha.get("grupo")
                espaco = grupo.espaco if grupo else dados["espaco"]
                if espaco is None:
                    raise ValidationError("Selecione o espaço para a aula individual.")
                reserva = SolicitacaoReserva(
                    atleta=atleta, profissional=dados["profissional"], espaco=espaco,
                    inicio=escolha["inicio"], fim=grupo.fim if grupo else escolha["fim"],
                    grupo=grupo,
                )
                if atleta.idade < 18 and atleta.responsavel.usuario.user_id != request.user.pk:
                    _, criada = SolicitacaoReserva.objects.get_or_create(
                        atleta=atleta, profissional=reserva.profissional, inicio=reserva.inicio,
                        situacao=SolicitacaoReserva.Situacao.PENDENTE,
                        defaults={"espaco": espaco, "fim": reserva.fim, "grupo": grupo},
                    )
                    mensagem = ("Solicitação enviada ao responsável." if criada else
                                "Já existe uma solicitação aguardando autorização para esse horário.")
                else:
                    confirmar_reserva(reserva)
                    mensagem = "Aula agendada com sucesso."
            except ValidationError as erro:
                form.add_error(None, erro.messages)
            else:
                messages.success(request, mensagem)
                return redirect("portal")
    return render(
        request, "agendamentos/portal_reserva.html", {"form": form, "opcoes": opcoes}
    )


@login_required
def minhas_aulas(request):
    participacoes = (
        ParticipacaoAgendamento.objects.filter(
            Q(atleta__usuario__user=request.user)
            | Q(atleta__responsavel__usuario__user=request.user)
        )
        .select_related(
            "atleta", "agendamento__profissional__usuario__user", "agendamento__espaco"
        )
        .order_by("-agendamento__inicio", "-id")
    )
    solicitacoes = SolicitacaoReserva.objects.filter(
        Q(atleta__usuario__user=request.user) | Q(atleta__responsavel__usuario__user=request.user)
    ).select_related("atleta__responsavel__usuario", "profissional__usuario__user", "espaco", "decidida_por")
    return render(request, "agendamentos/portal.html", {
        "participacoes": participacoes, "solicitacoes": solicitacoes, "portal_decisao": True,
    })


def confirmar_reserva(reserva):
    if reserva.inicio <= timezone.now() or not reserva.profissional.ativo:
        raise ValidationError("O horário ou profissional não está mais disponível.")
    if reserva.grupo_id:
        grupo = reserva.grupo
        if (grupo.inicio, grupo.fim, grupo.espaco_id, grupo.profissional_id) != (
            reserva.inicio, reserva.fim, reserva.espaco_id, reserva.profissional_id
        ):
            raise ValidationError("A turma foi alterada. Faça uma nova solicitação.")
        return inscrever_em_atividade_grupo(
            agendamento=grupo, atleta=reserva.atleta
        ).agendamento
    return criar_agendamento(
        profissional=reserva.profissional, espaco=reserva.espaco,
        atletas=[reserva.atleta], registrado_por=None, inicio=reserva.inicio, fim=reserva.fim,
    )


@login_required
@require_POST
def decidir_reserva(request, pk):
    autorizada = request.POST.get("decisao") == "autorizar"
    if request.POST.get("decisao") not in {"autorizar", "recusar"}:
        messages.error(request, "Selecione uma decisão válida.")
        return redirect("portal")

    try:
        with transaction.atomic():
            reserva = get_object_or_404(
                SolicitacaoReserva.objects.select_related(
                    "atleta__responsavel", "profissional", "espaco", "grupo"
                ),
                pk=pk, atleta__responsavel__usuario__user=request.user,
            )
            alteradas = SolicitacaoReserva.objects.filter(
                pk=pk, situacao=SolicitacaoReserva.Situacao.PENDENTE,
                atleta__responsavel__usuario__user=request.user,
            ).update(
                situacao=(SolicitacaoReserva.Situacao.AUTORIZADA if autorizada
                          else SolicitacaoReserva.Situacao.RECUSADA),
                decidida_por=reserva.atleta.responsavel, decidida_em=timezone.now(),
            )
            if not alteradas:
                raise ValidationError("Esta solicitação já foi respondida.")
            if autorizada:
                reserva.agendamento_confirmado = confirmar_reserva(reserva)
                reserva.save(update_fields=["agendamento_confirmado"])
    except ValidationError as erro:
        messages.error(request, " ".join(erro.messages))
    else:
        mensagens = "Aula autorizada e confirmada." if autorizada else "Solicitação recusada e cancelada."
        messages.success(request, mensagens)
    return redirect("portal")
