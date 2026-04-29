from django.shortcuts import render, get_object_or_404
from ..models import PrestadorPerfil, Avaliacao


def perfil_prestador(request, slug):
    """
    Página de perfil público de um prestador de serviço.
    Exibe bio, especialidades, valor/hora, avaliações e botão de contratação.
    """
    prestador = get_object_or_404(PrestadorPerfil, slug=slug)
    avaliacoes = Avaliacao.objects.filter(
        prestador=prestador
    ).select_related('cliente').order_by('-criado_em')[:10]

    # Estrelas para exibição visual (range de 1 a 5)
    estrelas_range = range(1, 6)

    context = {
        'prestador': prestador,
        'avaliacoes': avaliacoes,
        'estrelas_range': estrelas_range,
        'titulo_aba': f'{prestador.user.get_full_name() or prestador.user.username} | ServiçosHub',
        'mostrar_busca': False,
    }
    return render(request, 'servicos/perfil_prestador.html', context)

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from ..forms import EditarPerfilPrestadorForm

@login_required
def editar_perfil(request):
    """
    Página para o prestador editar seu próprio perfil (front-end).
    Se o perfil não existir, ele é criado implicitamente.
    """
    # Obtém ou cria o perfil atrelado ao usuário
    perfil, created = PrestadorPerfil.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = EditarPerfilPrestadorForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('servicos:meu_painel')
    else:
        form = EditarPerfilPrestadorForm(instance=perfil)
        
    context = {
        'form': form,
        'titulo_aba': 'Editar Perfil | ServiçosHub',
        'mostrar_busca': False,
    }
    return render(request, 'servicos/editar_perfil.html', context)
