from django import forms
from django.contrib import admin

from .models import (
    Atleta,
    Funcionario,
    Profissional,
    Responsavel,
    Usuario,
)


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
        "id", "nome", "usuario", "data_de_nascimento", "idade", "ativo", "responsavel"
    )
    list_filter = ("ativo",)
    search_fields = ("nome", "usuario__user__username")


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "especialidade", "ativo")
    list_filter = ("ativo",)


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "cargo", "ativo")
    list_filter = ("ativo",)
