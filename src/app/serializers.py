# app/serializers.py
from rest_framework import serializers
from app.models import Produto
from app.models import Espaco
from app.models import Equipamento

class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = ['id', 'nome', 'preco', 'descricao', 'disponivel']
        read_only_fields = ['id']