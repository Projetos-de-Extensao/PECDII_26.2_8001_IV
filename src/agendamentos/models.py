from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Agendamento(models.Model):
    class Situacao(models.TextChoices):
        AGENDADO = "agendado", "Agendado"
        CANCELADO = "cancelado", "Cancelado"
        REALIZADO = "realizado", "Realizado"

    profissional = models.ForeignKey(
        "usuarios.Profissional",
        on_delete=models.PROTECT,
        related_name="agendamentos",
    )
    espaco = models.ForeignKey(
        "app.Espaco",
        on_delete=models.PROTECT,
        related_name="agendamentos",
    )
    atletas = models.ManyToManyField(
        "usuarios.Atleta",
        related_name="agendamentos",
        through="ParticipacaoAgendamento",
        through_fields=("agendamento", "atleta"),
    )
    equipamentos = models.ManyToManyField(
        "app.Equipamento",
        related_name="agendamentos",
        blank=True,
    )
    registrado_por = models.ForeignKey(
        "usuarios.Funcionario",
        on_delete=models.PROTECT,
        related_name="agendamentos_registrados",
    )
    inicio = models.DateTimeField()
    fim = models.DateTimeField()
    situacao = models.CharField(
        max_length=20,
        choices=Situacao.choices,
        default=Situacao.AGENDADO,
    )
    observacoes = models.TextField(blank=True)
    motivo_cancelamento = models.TextField(blank=True)
    cancelado_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("inicio", "id")
        indexes = [
            models.Index(fields=("inicio", "fim")),
            models.Index(fields=("profissional", "inicio", "fim")),
            models.Index(fields=("espaco", "inicio", "fim")),
        ]

    def clean(self):
        super().clean()

        erros = {}

        inicio_valido = self.inicio is not None
        fim_valido = self.fim is not None

        if inicio_valido and timezone.is_naive(self.inicio):
            erros["inicio"] = "Informe o horário inicial com fuso horário."
            inicio_valido = False

        if fim_valido and timezone.is_naive(self.fim):
            erros["fim"] = "Informe o horário final com fuso horário."
            fim_valido = False

        if inicio_valido and fim_valido:
            inicio_local = timezone.localtime(self.inicio)
            fim_local = timezone.localtime(self.fim)

            if self.fim <= self.inicio:
                erros["fim"] = (
                    "O horário final deve ser posterior ao horário inicial."
                )
            elif inicio_local.date() != fim_local.date():
                erros["fim"] = (
                    "O agendamento deve começar e terminar no mesmo dia."
                )

        if self.profissional_id and not self.profissional.ativo:
            erros["profissional"] = (
                "O profissional precisa estar ativo para receber agendamentos."
            )

        if self.registrado_por_id and not self.registrado_por.ativo:
            erros["registrado_por"] = (
                "O funcionário precisa estar ativo para registrar agendamentos."
            )

        if erros:
            raise ValidationError(erros)

    def __str__(self):
        return (
            f"{self.inicio:%d/%m/%Y %H:%M} - "
            f"{self.profissional} - {self.espaco}"
        )


class ParticipacaoAgendamento(models.Model):
    class Situacao(models.TextChoices):
        CONFIRMADA = "confirmada", "Confirmada"
        CANCELADA = "cancelada", "Cancelada"
        PRESENTE = "presente", "Presente"
        FALTA = "falta", "Falta"
        FALTA_JUSTIFICADA = "falta_justificada", "Falta justificada"

    agendamento = models.ForeignKey(
        Agendamento,
        on_delete=models.CASCADE,
        related_name="participacoes",
    )
    atleta = models.ForeignKey(
        "usuarios.Atleta",
        on_delete=models.PROTECT,
        related_name="participacoes_agendamento",
    )
    situacao = models.CharField(
        max_length=20,
        choices=Situacao.choices,
        default=Situacao.CONFIRMADA,
    )
    observacoes = models.TextField(blank=True)
    motivo_cancelamento = models.TextField(blank=True)
    cancelado_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("agendamento", "atleta")
        constraints = [
            models.UniqueConstraint(
                fields=("agendamento", "atleta"),
                name="participacao_unica_por_agendamento_atleta",
            ),
        ]
        indexes = [
            models.Index(fields=("atleta", "situacao")),
        ]

    def __str__(self):
        return f"{self.atleta} - {self.get_situacao_display()}"
