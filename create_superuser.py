import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from usuarios.models import Usuario
from empresas.models import Empresa

def seed():
    if not Empresa.objects.exists():
        empresa = Empresa.objects.create(
            razao_social='Minha Empresa Teste LTDA',
            nome_fantasia='PDV Cloud - Loja 1',
            cnpj='00000000000100',
            email='contato@minhaempresa.com.br'
        )
        print(f"Empresa '{empresa.nome_fantasia}' criada com sucesso!")
    else:
        empresa = Empresa.objects.first()
        print("Empresa já existe.")

    if not Usuario.objects.filter(username='admin').exists():
        user = Usuario.objects.create_superuser(
            username='admin',
            email='admin@pdv.com',
            password='admin',
            role='admin',
            empresa=empresa
        )
        print(f"Usuário '{user.username}' criado com sucesso! (Senha: admin)")
    else:
        print("Usuário 'admin' já existe.")

if __name__ == '__main__':
    seed()
