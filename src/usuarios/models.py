
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def validar_telefone_informado(telefone):
    """Verifica se o telefone possui pelo menos 11 dígitos."""
    numeros = "".join(
        caractere for caractere in telefone
        if caractere.isdigit()
    )
    return len(numeros) >= 11


class Usuario(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="perfil"
    )

    telefone = models.CharField(
        max_length=20,
        blank=True
    )

    def clean(self):
        super().clean()

        if self.telefone and not validar_telefone_informado(self.telefone):
            raise ValidationError({
                "telefone": "O telefone deve conter pelo menos 11 dígitos."
            })

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Responsavel(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.PROTECT,
        related_name="responsavel"
    )

    telefone = models.CharField(
        max_length=20,
        blank=True
    )

    def clean(self):
        super().clean()

        if self.telefone and not validar_telefone_informado(self.telefone):
            raise ValidationError({
                "telefone": "O telefone deve conter pelo menos 11 dígitos."
            })

    def __str__(self):
        return str(self.usuario)


class Atleta(models.Model):
    nome = models.CharField(max_length=150)

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.PROTECT,
        related_name="atleta",
        null=True,
        blank=True
    )

    data_de_nascimento = models.DateField(
        null=True,
        blank=True
    )

    telefone = models.CharField(
        max_length=20,
        blank=True
    )

    objetivos = models.TextField(blank=True)

    ativo = models.BooleanField(default=True)

    responsavel = models.ForeignKey(
        Responsavel,
        on_delete=models.PROTECT,
        related_name="atletas",
        null=True,
        blank=True
    )

    @property
    def idade(self):
        if self.data_de_nascimento is None:
            return None

        hoje = timezone.localdate()
        nascimento = self.data_de_nascimento

        return (
            hoje.year - nascimento.year
            - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
        )

    def clean(self):
        super().clean()

        if (
            self.data_de_nascimento is not None
            and self.data_de_nascimento > timezone.localdate()
        ):
            raise ValidationError({
                "data_de_nascimento": "A data de nascimento não pode ser futura."
            })

        if self.telefone and not validar_telefone_informado(self.telefone):
            raise ValidationError({
                "telefone": "O telefone deve conter pelo menos 11 dígitos."
            })

    def validar_para_agendamento(self):
        """Verifica se o atleta está apto a realizar agendamentos."""

        self.full_clean()

        erros = {}

        if self.pk is None:
            erros["__all__"] = (
                "Salve o cadastro do atleta antes de agendar."
            )

        if self.data_de_nascimento is None:
            erros["data_de_nascimento"] = (
                "Informe a data de nascimento antes de agendar."
            )

        elif self.idade < 18 and self.responsavel_id is None:
            erros["responsavel"] = (
                "Atletas menores de 18 anos precisam de um responsável "
                "para realizar agendamentos."
            )

        if erros:
            raise ValidationError(erros)

    def __str__(self):
        return self.nome


class Profissional(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.PROTECT,
        related_name="profissional"
    )

    especialidade = models.CharField(max_length=100)

    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.usuario} - {self.especialidade}"


class Funcionario(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.PROTECT,
        related_name="funcionario"
    )

    cargo = models.CharField(max_length=100)

    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.usuario} - {self.cargo}"


class DisponibilidadeProfissional(models.Model):
    DIAS_SEMANA = [
        (0, "Segunda-feira"),
        (1, "Terça-feira"),
        (2, "Quarta-feira"),
        (3, "Quinta-feira"),
        (4, "Sexta-feira"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        related_name="disponibilidades"
    )

    dia_semana = models.IntegerField(
        choices=DIAS_SEMANA
    )

    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()

    def clean(self):
        super().clean()

        if (
            self.hora_inicio is not None
            and self.hora_fim is not None
            and self.hora_fim <= self.hora_inicio
        ):
            raise ValidationError({
                "hora_fim": "O horário final deve ser posterior ao inicial."
            })
