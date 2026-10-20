
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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

        if self.telefone:
            numeros = "".join(i for i in self.telefone if i.isdigit()
                              )
            if len(numeros) < 11:
                raise ValidationError({
                    "telefone":
                    "O telefone deve conter pelo menos 11 dígitos."
                })
            
    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Responsavel(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.PROTECT,
        related_name="responsavel"
    )

    def __str__(self):
        return str(self.usuario)


class Atleta(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.PROTECT,
        related_name="atleta"
    )

    data_de_nascimento = models.DateField()

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
        hoje = timezone.localdate()
        nascimento = self.data_de_nascimento

        return (
            hoje.year - nascimento.year
            - ((hoje.month, hoje.day)
               < (nascimento.month, nascimento.day))
        )

    def clean(self):
        super().clean()

        if self.data_de_nascimento is None:
            return

        if self.data_de_nascimento > timezone.localdate():
            raise ValidationError({
                "data_de_nascimento":
                "A data de nascimento não pode ser futura."
            })

        if self.idade < 18 and self.responsavel_id is None:
            raise ValidationError({
                "responsavel":
                "Atletas menores de idade precisam de um responsável."
            })

    def __str__(self):
        return str(self.usuario)


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
                "hora_fim":
                "O horário final deve ser posterior ao inicial."
            })
