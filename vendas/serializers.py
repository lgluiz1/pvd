from rest_framework import serializers
from vendas.models import Venda, ItemVenda


class ItemVendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemVenda
        fields = [
            'id', 'produto', 'produto_nome', 'quantidade',
            'valor_unitario', 'desconto', 'subtotal',
        ]
        read_only_fields = ['id', 'subtotal']


class VendaSerializer(serializers.ModelSerializer):
    itens = ItemVendaSerializer(many=True, read_only=True)
    operador_nome = serializers.CharField(source='operador.get_full_name', read_only=True, default='')
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True, default='')

    class Meta:
        model = Venda
        fields = [
            'id', 'numero', 'operador', 'operador_nome',
            'cliente', 'cliente_nome', 'sessao_caixa',
            'subtotal', 'desconto_tipo', 'desconto_valor', 'total',
            'forma_pagamento', 'valor_recebido', 'troco',
            'status', 'cancelada_por', 'motivo_cancelamento',
            'pdv_terminal', 'sync_status', 'observacoes',
            'itens', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
