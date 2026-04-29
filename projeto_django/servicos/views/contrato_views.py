from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from ..models import PrestadorPerfil, Contrato
from ..forms import SolicitacaoServicoForm


@login_required
def solicitar_servico(request, slug):
    """
    Formulário de solicitação de demanda para um prestador específico.
    Cria um Contrato com status PENDENTE.
    """
    prestador = get_object_or_404(PrestadorPerfil, slug=slug, disponivel=True, status_adesao='ATIVO')

    if request.method == 'POST':
        form = SolicitacaoServicoForm(request.POST)
        if form.is_valid():
            contrato = form.save(commit=False)
            contrato.cliente = request.user
            contrato.prestador = prestador
            contrato.categoria = prestador.especialidades.first()
            # Calcula valor estimado baseado no valor/hora do prestador
            horas = form.cleaned_data.get('horas_estimadas', 1)
            contrato.valor_acordado = prestador.valor_hora * horas
            contrato.status = 'PENDENTE'
            contrato.status_pagamento = 'AGUARDANDO'
            contrato.save()
            messages.success(
                request,
                f'✅ Solicitação enviada com sucesso! O prestador será notificado. '
                f'Valor estimado: R$ {contrato.valor_acordado:.2f}'
            )
            return redirect('servicos:meu_painel')
    else:
        form = SolicitacaoServicoForm()

    context = {
        'form': form,
        'prestador': prestador,
        'titulo_aba': f'Solicitar Serviço — {prestador.user.get_full_name() or prestador.user.username}',
        'mostrar_busca': False,
    }
    return render(request, 'servicos/solicitar_servico.html', context)


@login_required
def meu_painel(request):
    """
    Painel central do usuário. Mostra contratos como cliente E como prestador.
    """
    user = request.user

    # Contratos onde o usuário é CLIENTE
    contratos_cliente = Contrato.objects.filter(
        cliente=user
    ).select_related('prestador__user', 'categoria').order_by('-data_solicitacao')

    # Contratos onde o usuário é PRESTADOR
    contratos_prestador = []
    prestador_perfil = None
    try:
        prestador_perfil = user.prestador_perfil
        contratos_prestador = Contrato.objects.filter(
            prestador=prestador_perfil
        ).select_related('cliente', 'categoria').order_by('-data_solicitacao')
    except PrestadorPerfil.DoesNotExist:
        pass

    # Agrupamento de contratos do cliente por status para exibição
    status_grupos = {
        'PENDENTE': contratos_cliente.filter(status='PENDENTE'),
        'ACEITO': contratos_cliente.filter(status='ACEITO'),
        'EM_EXECUCAO': contratos_cliente.filter(status='EM_EXECUCAO'),
        'CONCLUIDO': contratos_cliente.filter(status='CONCLUIDO'),
        'CANCELADO': contratos_cliente.filter(status='CANCELADO'),
    }

    context = {
        'contratos_cliente': contratos_cliente,
        'contratos_prestador': contratos_prestador,
        'prestador_perfil': prestador_perfil,
        'status_grupos': status_grupos,
        'titulo_aba': 'Meu Painel | ServiçosHub',
        'mostrar_busca': False,
    }
    return render(request, 'servicos/meu_painel.html', context)


@login_required
def atualizar_status_contrato(request, contrato_id, novo_status):
    """
    Atualiza o status de um contrato. Acessível apenas pelo prestador responsável.
    Status permitidos: ACEITO, EM_EXECUCAO, CONCLUIDO, CANCELADO.
    """
    TRANSICOES_VALIDAS = {
        'PENDENTE': ['ACEITO', 'CANCELADO'],
        'ACEITO': ['EM_EXECUCAO', 'CANCELADO'],
        'EM_EXECUCAO': ['CONCLUIDO', 'DISPUTADO'],
    }
    STATUS_PAGAMENTO_MAP = {
        'ACEITO': 'RETIDO',
        'CONCLUIDO': 'LIBERADO',
        'CANCELADO': 'REEMBOLSADO',
    }

    contrato = get_object_or_404(Contrato, pk=contrato_id)

    # Verifica se o usuário logado é o prestador do contrato
    try:
        if contrato.prestador.user != request.user:
            messages.error(request, 'Você não tem permissão para alterar este contrato.')
            return redirect('servicos:meu_painel')
    except Exception:
        messages.error(request, 'Acesso negado.')
        return redirect('servicos:meu_painel')

    status_atual = contrato.status
    transicoes = TRANSICOES_VALIDAS.get(status_atual, [])

    if novo_status not in transicoes:
        messages.error(request, f'Transição de "{status_atual}" para "{novo_status}" não é permitida.')
        return redirect('servicos:meu_painel')

    # Aplica timestamps de acordo com o status
    agora = timezone.now()
    if novo_status == 'ACEITO':
        contrato.data_aceite = agora
    elif novo_status == 'EM_EXECUCAO':
        contrato.data_inicio = agora
    elif novo_status == 'CONCLUIDO':
        contrato.data_conclusao = agora
        # Incrementa contador do prestador
        prestador = contrato.prestador
        prestador.total_servicos += 1
        prestador.save(update_fields=['total_servicos'])

    contrato.status = novo_status
    # Atualiza pagamento/escrow automaticamente
    if novo_status in STATUS_PAGAMENTO_MAP:
        contrato.status_pagamento = STATUS_PAGAMENTO_MAP[novo_status]

    contrato.save()

    labels_status = {
        'ACEITO': 'aceito ✅',
        'EM_EXECUCAO': 'iniciado 🔧',
        'CONCLUIDO': 'concluído 🎉',
        'CANCELADO': 'cancelado ❌',
    }
    messages.success(request, f'Contrato #{contrato_id} {labels_status.get(novo_status, "atualizado")}!')
    return redirect('servicos:meu_painel')
