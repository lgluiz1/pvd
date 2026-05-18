from rest_framework import serializers
from financeiro.models import ContaFiado, ParcelaFiado, PagamentoFiado

class ContaFiadoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    disponivel = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    class Meta:
        model = ContaFiado
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class ParcelaFiadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParcelaFiado
        fields = '__all__'

class PagamentoFiadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagamentoFiado
        fields = '__all__'
