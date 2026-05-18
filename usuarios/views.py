from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from usuarios.models import Usuario


def login_view(request):
    """Tela de login."""
    if request.user.is_authenticated:
        return redirect('relatorios:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                next_url = request.GET.get('next', 'relatorios:dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Conta desativada.')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')

    return render(request, 'usuarios/login.html', {
        'page_title': 'Login',
    })


def logout_view(request):
    """Logout."""
    logout(request)
    return redirect('usuarios:login')


@login_required
def usuario_lista(request):
    """Lista de usuários da empresa."""
    if not request.user.is_admin:
        messages.error(request, 'Acesso negado.')
        return redirect('relatorios:dashboard')

    usuarios = Usuario.objects.filter(empresa=request.empresa)
    return render(request, 'usuarios/lista.html', {
        'usuarios': usuarios,
        'page_title': 'Usuários',
    })


@login_required
def usuario_criar(request):
    """Criar novo usuário."""
    if not request.user.is_admin:
        messages.error(request, 'Acesso negado.')
        return redirect('relatorios:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'operador')
        telefone = request.POST.get('telefone', '').strip()

        if Usuario.objects.filter(username=username).exists():
            messages.error(request, 'Nome de usuário já existe.')
        else:
            user = Usuario(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                role=role,
                telefone=telefone,
                empresa=request.empresa,
            )
            user.set_password(password)
            user.save()
            messages.success(request, f'Usuário {username} criado com sucesso!')
            return redirect('usuarios:lista')

    return render(request, 'usuarios/form.html', {
        'page_title': 'Novo Usuário',
    })


@login_required
def usuario_editar(request, pk):
    """Editar usuário."""
    if not request.user.is_admin:
        messages.error(request, 'Acesso negado.')
        return redirect('relatorios:dashboard')

    usuario = get_object_or_404(Usuario, pk=pk, empresa=request.empresa)

    if request.method == 'POST':
        usuario.first_name = request.POST.get('first_name', usuario.first_name)
        usuario.last_name = request.POST.get('last_name', usuario.last_name)
        usuario.email = request.POST.get('email', usuario.email)
        usuario.role = request.POST.get('role', usuario.role)
        usuario.telefone = request.POST.get('telefone', usuario.telefone)
        usuario.is_active = request.POST.get('is_active') == 'on'

        new_password = request.POST.get('password', '').strip()
        if new_password:
            usuario.set_password(new_password)

        usuario.save()
        messages.success(request, 'Usuário atualizado com sucesso!')
        return redirect('usuarios:lista')

    return render(request, 'usuarios/form.html', {
        'usuario': usuario,
        'page_title': f'Editar {usuario.get_full_name()}',
        'editando': True,
    })
