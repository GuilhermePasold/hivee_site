from django.db.models import Q
from django.shortcuts import render, redirect

from ..models import Produto


def listar_produtos(request):
    termo_busca = request.GET.get('q', '').strip()

    produtos = Produto.objects.filter(disponivel=True).select_related('categoria')

    if termo_busca:
        produtos = produtos.filter(
            Q(nome__icontains=termo_busca)
            | Q(descricao__icontains=termo_busca)
            | Q(categoria__nome__icontains=termo_busca)
        )

    context = {
        'produtos': produtos.distinct(),
        'termo_busca': termo_busca,
    }
    return render(request, 'index.html', context)


def listar_prestadores(request):
    return listar_produtos(request)

