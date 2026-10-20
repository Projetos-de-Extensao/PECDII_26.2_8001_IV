from django import forms
from django.contrib import admin

from .models import (
    Usuario,
    Responsavel,
    Atleta,
    Profissional,
    Funcionario,
)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "telefone")
    search_fields = ("user__username", "user__email")


@admin.register(Responsavel)
class ResponsavelAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario")


class AtletaAdminForm(forms.ModelForm):
    data_de_nascimento = forms.DateField(
        input_formats=["%d/%m/%Y"],
        widget=forms.DateInput(
            format="%d/%m/%Y",
            attrs={
                "placeholder": "dd/mm/aaaa"
            }
        )
    )

    class Meta:
        model = Atleta
        fields = "__all__"

@admin.register(Atleta)
class AtletaAdmin(admin.ModelAdmin):
    form = AtletaAdminForm
    
    list_display = (
        "id",
        "usuario",
        "data_de_nascimento",
        "idade",
        "responsavel",
        "ativo",
    )
    list_filter = ("ativo",)


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "usuario",
        "especialidade",
        "ativo",
    )
    list_filter = ("ativo",)


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "usuario",
        "cargo",
        "ativo",
    )
    list_filter = ("ativo",)
