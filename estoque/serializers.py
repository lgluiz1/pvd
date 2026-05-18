from rest_framework import serializers
from estoque.models import MovimentacaoEstoque


class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)

    class Meta:
        model = MovimentacaoEstoque
        fields = [
            'id', 'produto', 'produto_nome', 'tipo', 'quantidade',
            'quantidade_anterior', 'quantidade_posterior',
            'motivo', 'usuario', 'referencia_venda', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
