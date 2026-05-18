from rest_framework import serializers
from empresas.models import Empresa, PDVTerminal


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = [
            'id', 'razao_social', 'nome_fantasia', 'cnpj',
            'telefone', 'email', 'endereco', 'ativo',
            'config_juros_mensal', 'config_juros_atraso',
            'config_multa_fixa', 'config_dias_tolerancia',
            'pix_chave', 'pix_tipo', 'pix_nome', 'pix_cidade',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmpresaResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ['id', 'nome_fantasia', 'cnpj']


class PDVTerminalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PDVTerminal
        fields = [
            'id', 'empresa', 'identificador', 'nome',
            'ativo', 'ultimo_sync', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
