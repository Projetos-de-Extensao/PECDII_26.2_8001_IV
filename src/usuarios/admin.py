from datetime import datetime, time, timedelta

from django import forms
from django.contrib import admin

from .models import (
    Atleta,
    DisponibilidadeProfissional,
    Funcionario,
    Profissional,
    Responsavel,
    Usuario,
)


def opcoes_horarios(hora_inicial, hora_final):
    atual = datetime.combine(datetime.today(), hora_inicial)
    fim = datetime.combine(datetime.today(), hora_final)
    opcoes = []
    while atual <= fim:
        valor = atual.strftime("%H:%M")
        opcoes.append((valor, valor))
        atual += timedelta(minutes=30)
    return opcoes


OPCOES_INICIO = [
    ("", "---------"),
    *opcoes_horarios(time(7, 0), time(11, 30)),
    *opcoes_horarios(time(13, 0), time(19, 30)),
]
OPCOES_FIM = [
    ("", "---------"),
    *opcoes_horarios(time(7, 30), time(12, 0)),
    *opcoes_horarios(time(13, 30), time(20, 0)),
]


class DisponibilidadeProfissionalInlineForm(forms.ModelForm):
    hora_inicio = forms.TimeField(
        label="Início",
        input_formats=("%H:%M",),
        widget=forms.Select(choices=OPCOES_INICIO),
    )
    hora_fim = forms.TimeField(
        label="Fim",
        input_formats=("%H:%M",),
        widget=forms.Select(choices=OPCOES_FIM),
    )

    class Meta:
        model = DisponibilidadeProfissional
        fields = ("dia_semana", "hora_inicio", "hora_fim")


class DisponibilidadeProfissionalInline(admin.TabularInline):
    model = DisponibilidadeProfissional
    form = DisponibilidadeProfissionalInlineForm
    fields = ("dia_semana", "hora_inicio", "hora_fim")
    extra = 1
    verbose_name = "horário disponível"
    verbose_name_plural = "Horários disponíveis"


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "telefone")
    search_fields = ("user__username", "user__email")


@admin.register(Responsavel)
class ResponsavelAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "telefone")

    search_fields = (
        "usuario__user__first_name",
        "usuario__user__last_name",
        "usuario__user__username",
        "telefone",
    )


class AtletaAdminForm(forms.ModelForm):
    data_de_nascimento = forms.DateField(
        required=False,
        input_formats=["%d/%m/%Y"],
        widget=forms.DateInput(
            format="%d/%m/%Y",
            attrs={"placeholder": "dd/mm/aaaa"},
        ),
    )

    class Meta:
        model = Atleta
        fields = "__all__"


@admin.register(Atleta)
class AtletaAdmin(admin.ModelAdmin):
    form = AtletaAdminForm
    list_display = (
        "id",
        "nome",
        "email",
        "usuario",
        "data_de_nascimento",
        "idade",
        "ativo",
        "responsavel",
    )
    list_filter = ("ativo",)
    search_fields = (
        "nome",
        "email",
        "telefone",
        "usuario__user__username",
    )


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "especialidade", "ativo")
    list_filter = ("ativo",)
    inlines = (DisponibilidadeProfissionalInline,)


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "cargo", "ativo")
    list_filter = ("ativo",)
