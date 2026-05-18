from rest_framework import serializers
from fornecedores.models import Fornecedor

class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = ['id', 'nome', 'cnpj', 'telefone', 'email', 'endereco', 'contato', 'observacoes', 'ativo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
