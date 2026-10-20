from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    descricao = models.TextField()
    disponivel = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class Espaco(models.Model):
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)
    capacidade = models.PositiveIntegerField()

    def comporta(self, quantidade_atletas):
        return 0 < quantidade_atletas <= self.capacidade

    def __str__(self):
        return f"{self.nome} - {self.tipo}"


class Equipamento(models.Model):
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nome} - {self.tipo}"