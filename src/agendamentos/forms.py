from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from app.models import Equipamento, Espaco
from usuarios.models import Atleta, Funcionario, Profissional

from .models import Agendamento


class AgendamentoForm(forms.Form):
    profissional = forms.ModelChoiceField(
        label="Profissional",
        queryset=Profissional.objects.none(),
        empty_label="Selecione um profissional",
    )
    espaco = forms.ModelChoiceField(
        label="Espaço",
        queryset=Espaco.objects.none(),
        empty_label="Selecione um espaço",
        required=False,
    )
    modalidade = forms.ChoiceField(
        label="Modalidade",
        choices=Agendamento.Modalidade.choices,
        initial=Agendamento.Modalidade.INDIVIDUAL,
        required=False,
    )
    limite_participantes = forms.IntegerField(
        label="Limite de participantes",
        min_value=1,
        initial=1,
        required=False,
        help_text="Definido pelo profissional para atividades em grupo.",
    )
    atletas = forms.ModelMultipleChoiceField(
        label="Atletas",
        queryset=Atleta.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        help_text="Marque um atleta para aula individual ou vários para grupo.",
        required=False,
    )
    novo_atleta = forms.BooleanField(
        label="Cadastrar novo interessado",
        required=False,
        widget=forms.HiddenInput(),
        help_text=(
            "Cria um atleta sem usuário ou senha e registra sua aula "
            "experimental."
        ),
    )
    aula_experimental = forms.BooleanField(
        label="Aula experimental",
        required=False,
        widget=forms.HiddenInput(),
        help_text=(
            "Permitida uma única vez; um cancelamento libera a remarcação."
        ),
    )
    novo_atleta_nome = forms.CharField(
        label="Nome completo",
        max_length=150,
        required=False,
    )
    novo_atleta_email = forms.EmailField(
        label="E-mail",
        required=False,
    )
    novo_atleta_telefone = forms.CharField(
        label="Telefone",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "(00) 00000-0000"}),
    )
    novo_atleta_data_de_nascimento = forms.DateField(
        label="Data de nascimento",
        required=False,
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    equipamentos = forms.ModelMultipleChoiceField(
        label="Equipamentos",
        queryset=Equipamento.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Opcional.",
    )
    registrado_por = forms.ModelChoiceField(
        label="Registrado por",
        queryset=Funcionario.objects.none(),
        empty_label="Selecione um funcionário",
        required=False,
        help_text="Funcionário responsável por lançar o agendamento.",
    )
    data = forms.DateField(
        label="Data",
        initial=timezone.localdate,
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    inicio = forms.DateTimeField(
        label="Horário",
        input_formats=("%Y-%m-%dT%H:%M",),
        widget=forms.HiddenInput(),
    )
    fim = forms.DateTimeField(
        label="Fim",
        input_formats=("%Y-%m-%dT%H:%M",),
        widget=forms.HiddenInput(),
    )
    agendamento_grupo = forms.ModelChoiceField(
        queryset=Agendamento.objects.none(),
        required=False,
        widget=forms.HiddenInput(),
    )
    observacoes = forms.CharField(
        label="Observações",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["profissional"].queryset = (
            Profissional.objects.filter(ativo=True)
            .select_related("usuario__user")
            .order_by("usuario__user__first_name", "usuario__user__username")
        )
        self.fields["espaco"].queryset = Espaco.objects.order_by("nome")
        self.fields["atletas"].queryset = Atleta.objects.filter(
            ativo=True
        ).order_by("nome")
        self.fields["equipamentos"].queryset = Equipamento.objects.order_by(
            "nome"
        )
        self.fields["registrado_por"].queryset = (
            Funcionario.objects.filter(ativo=True)
            .select_related("usuario__user")
            .order_by("usuario__user__first_name", "usuario__user__username")
        )
        self.fields["agendamento_grupo"].queryset = (
            Agendamento.objects.filter(
                modalidade=Agendamento.Modalidade.GRUPO,
                situacao=Agendamento.Situacao.AGENDADO,
            )
        )

    def clean(self):
        dados = super().clean()
        profissional = dados.get("profissional")
        data = dados.get("data")
        inicio = dados.get("inicio")
        fim = dados.get("fim")
        grupo = dados.get("agendamento_grupo")
        atletas = dados.get("atletas")
        novo_atleta = dados.get("novo_atleta")
        aula_experimental = bool(novo_atleta)
        dados["aula_experimental"] = aula_experimental
        registrado_por = dados.get("registrado_por")

        if novo_atleta:
            if atletas:
                self.add_error(
                    "atletas",
                    "Escolha atletas existentes ou cadastre um novo, não ambos.",
                )

            campos_obrigatorios = {
                "novo_atleta_nome": "Informe o nome completo.",
                "novo_atleta_email": "Informe o e-mail.",
                "novo_atleta_telefone": "Informe o telefone.",
                "novo_atleta_data_de_nascimento": (
                    "Informe a data de nascimento."
                ),
            }
            for campo, mensagem in campos_obrigatorios.items():
                if not dados.get(campo):
                    self.add_error(campo, mensagem)

            candidato = Atleta(
                nome=dados.get("novo_atleta_nome") or "",
                email=dados.get("novo_atleta_email") or "",
                telefone=dados.get("novo_atleta_telefone") or "",
                data_de_nascimento=dados.get(
                    "novo_atleta_data_de_nascimento"
                ),
            )
            try:
                candidato.full_clean()
            except ValidationError as erro:
                mapa_campos = {
                    "nome": "novo_atleta_nome",
                    "email": "novo_atleta_email",
                    "telefone": "novo_atleta_telefone",
                    "data_de_nascimento": (
                        "novo_atleta_data_de_nascimento"
                    ),
                }
                for campo, mensagens in erro.message_dict.items():
                    destino = mapa_campos.get(campo)
                    for mensagem in mensagens:
                        self.add_error(destino, mensagem)

            if (
                candidato.data_de_nascimento
                and candidato.idade < 18
            ):
                self.add_error(
                    "novo_atleta_data_de_nascimento",
                    "Para menores de 18 anos, faça primeiro o cadastro "
                    "completo do atleta e do responsável.",
                )

        quantidade_atletas = 1 if novo_atleta else len(atletas or ())

        if aula_experimental and (
            registrado_por is None
            or registrado_por.cargo.strip().casefold() != "recepcionista"
        ):
            self.add_error(
                "registrado_por",
                "Selecione um recepcionista para registrar a experimental.",
            )

        if inicio and data and timezone.localtime(inicio).date() != data:
            self.add_error(
                "inicio",
                "O horário escolhido não pertence à data informada.",
            )

        if inicio and fim and fim - inicio != timedelta(minutes=30):
            self.add_error(
                "inicio",
                "Escolha um bloco de 30 minutos.",
            )

        if grupo:
            if profissional and grupo.profissional_id != profissional.pk:
                self.add_error(
                    "agendamento_grupo",
                    "A atividade não pertence ao profissional selecionado.",
                )
            if inicio and fim and (
                grupo.inicio >= fim or grupo.fim <= inicio
            ):
                self.add_error(
                    "agendamento_grupo",
                    "A atividade não pertence ao horário selecionado.",
                )
            if quantidade_atletas != 1:
                self.add_error(
                    "atletas",
                    "Selecione um atleta para entrar na atividade existente.",
                )
            return dados

        if not dados.get("espaco"):
            self.add_error("espaco", "Selecione um espaço.")
        if not dados.get("registrado_por"):
            self.add_error(
                "registrado_por",
                "Selecione o funcionário que está registrando.",
            )

        modalidade = dados.get("modalidade")
        limite = dados.get("limite_participantes")
        if modalidade == Agendamento.Modalidade.INDIVIDUAL:
            dados["limite_participantes"] = 1
            if quantidade_atletas != 1:
                self.add_error(
                    "atletas",
                    "Uma atividade individual deve possuir um atleta.",
                )
        elif modalidade == Agendamento.Modalidade.GRUPO:
            if quantidade_atletas < 1:
                self.add_error(
                    "atletas",
                    "Selecione pelo menos um atleta.",
                )
            if limite is None or limite < 2:
                self.add_error(
                    "limite_participantes",
                    "Informe um limite de pelo menos duas pessoas.",
                )

        return dados


class CancelamentoForm(forms.Form):
    motivo = forms.CharField(
        label="Motivo",
        required=False,
        max_length=500,
        widget=forms.TextInput(
            attrs={"placeholder": "Motivo do cancelamento (opcional)"}
        ),
    )
