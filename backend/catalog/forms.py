from django import forms
from django.contrib.auth.hashers import make_password

from .models import Cliente


class ClienteForm(forms.ModelForm):
    confirmar_senha = forms.CharField(
        label="Confirmar senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Cliente
        fields = ["nome", "cpf", "email", "telefone", "senha"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "cpf": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
            "senha": forms.PasswordInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()
        senha = cleaned.get("senha")
        confirmar = cleaned.get("confirmar_senha")
        if senha and confirmar and senha != confirmar:
            raise forms.ValidationError("As senhas nao conferem.")
        if senha:
            cleaned["senha"] = make_password(senha)
        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "seu@email.com"}
        )
    )
    senha = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Sua senha"}
        )
    )


class ClienteEditForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nome", "email", "telefone"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
        }
