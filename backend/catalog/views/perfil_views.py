from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..forms import ClienteEditForm
from ..models import Cliente


def checar_sessao(request):
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        return None
    return Cliente.objects.filter(id=cliente_id, ativo=True).first()


def editar_perfil(request):
    cliente = checar_sessao(request)
    if cliente is None:
        messages.error(request, "Entre para acessar seu perfil.")
        return redirect("catalog:login_cliente")

    if request.method == "POST":
        form = ClienteEditForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso.")
            return redirect("catalog:editar_perfil")
        messages.error(request, "Revise os dados do perfil.")
    else:
        form = ClienteEditForm(instance=cliente)

    return render(request, "catalog/perfil.html", {"form": form, "cliente": cliente})


@require_POST
def deletar_conta(request):
    cliente = checar_sessao(request)
    if cliente is None:
        messages.error(request, "Entre para continuar.")
        return redirect("catalog:login_cliente")

    cliente.ativo = False
    cliente.save(update_fields=["ativo", "atualizado_em"])
    request.session.pop("cliente_id", None)
    messages.success(request, "Conta desativada com sucesso.")
    return redirect("catalog:listar_prestadores")
