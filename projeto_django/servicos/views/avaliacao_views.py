from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from ..models import Contrato, Avaliacao
from ..forms import AvaliacaoForm


@login_required
def avaliar_contrato(request, contrato_id):
    """
    Permite ao cliente avaliar o prestador após conclusão do contrato.
    Atualiza a nota média do prestador automaticamente.
    """
    contrato = get_object_or_404(Contrato, pk=contrato_id, cliente=request.user, status='CONCLUIDO')

    # Verifica se já foi avaliado
    if hasattr(contrato, 'avaliacao'):
        messages.warning(request, 'Este contrato já foi avaliado.')
        return redirect('servicos:meu_painel')

    if request.method == 'POST':
        form = AvaliacaoForm(request.POST)
        if form.is_valid():
            avaliacao = form.save(commit=False)
            avaliacao.contrato = contrato
            avaliacao.cliente = request.user
            avaliacao.prestador = contrato.prestador
            avaliacao.save()

            # Recalcula nota média do prestador
            prestador = contrato.prestador
            media = Avaliacao.objects.filter(prestador=prestador).aggregate(
                media=Avg('estrelas')
            )['media'] or 0
            prestador.nota_media = round(media, 2)
            prestador.save(update_fields=['nota_media'])

            messages.success(request, '⭐ Obrigado pela avaliação! Ela ajuda outros clientes.')
            return redirect('servicos:meu_painel')
    else:
        form = AvaliacaoForm()

    context = {
        'form': form,
        'contrato': contrato,
        'titulo_aba': 'Avaliar Serviço | ServiçosHub',
        'mostrar_busca': False,
    }
    return render(request, 'servicos/avaliar.html', context)
