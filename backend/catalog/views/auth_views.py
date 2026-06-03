from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.shortcuts import redirect, render

from ..forms import ClienteForm, LoginForm
from ..models import Cliente


def cadastrar_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cadastro realizado com sucesso. Entre para continuar.")
            return redirect("catalog:login_cliente")
        messages.error(request, "Revise os dados do cadastro.")
    else:
        form = ClienteForm()

    return render(request, "catalog/cadastro.html", {"form": form})


def login_cliente(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            senha = form.cleaned_data["senha"]
            cliente = Cliente.objects.filter(email__iexact=email, ativo=True).first()
            if cliente and check_password(senha, cliente.senha):
                request.session["cliente_id"] = cliente.id
                messages.success(request, "Login realizado com sucesso.")
                return redirect("catalog:listar_prestadores")
            messages.error(request, "E-mail ou senha invalidos.")
    else:
        form = LoginForm()

    return render(request, "catalog/login.html", {"form": form})


def logout_cliente(request):
    if "cliente_id" in request.session:
        del request.session["cliente_id"]
    messages.success(request, "Voce saiu da sua conta.")
    return redirect("catalog:listar_prestadores")
