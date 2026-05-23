import re

from django import forms
from django.core.exceptions import ValidationError

from .models import Contrato, Avaliacao, PrestadorPerfil, UserProfile


def _normalize_digits(value):
    return re.sub(r'\D+', '', value or '')


def _format_cep(value):
    digits = _normalize_digits(value)
    if not digits:
        return ''
    if len(digits) != 8:
        raise ValidationError('CEP deve conter exatamente 8 números.')
    return f'{digits[:5]}-{digits[5:]}'


def _format_cpf(value):
    digits = _normalize_digits(value)
    if not digits:
        return ''
    if len(digits) != 11:
        raise ValidationError('CPF deve conter exatamente 11 números.')
    return f'{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}'


class SolicitacaoServicoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = ['titulo', 'descricao', 'endereco_servico', 'data_agendada', 'hora_agendada', 'horas_estimadas']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Conserto de torneira com vazamento'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Descreva o problema com detalhes. Quanto mais informações, melhor!'
            }),
            'endereco_servico': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Rua, número, bairro, cidade'
            }),
            'data_agendada': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'hora_agendada': forms.TimeInput(attrs={
                'class': 'form-input',
                'type': 'time'
            }),
            'horas_estimadas': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'max': 24
            }),
        }
        labels = {
            'titulo': 'Título do Serviço',
            'descricao': 'Descrição do Problema',
            'endereco_servico': 'Endereço do Serviço',
            'data_agendada': 'Data Preferida',
            'hora_agendada': 'Horário Preferido',
            'horas_estimadas': 'Horas Estimadas',
        }


class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = Avaliacao
        fields = ['estrelas', 'comentario']
        widgets = {
            'estrelas': forms.RadioSelect(attrs={'class': 'star-radio'}),
            'comentario': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Conte como foi a experiência com o prestador...'
            }),
        }
        labels = {
            'estrelas': 'Sua Avaliação',
            'comentario': 'Comentário (opcional)',
        }


class ClienteForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
        label='Nome completo',
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seuemail@exemplo.com'}),
        label='Email',
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'}),
        label='Senha',
    )
    cpf = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
        label='CPF',
    )
    cep = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000', 'maxlength': 9}),
        label='CEP',
    )

    def clean_cpf(self):
        return _format_cpf(self.cleaned_data.get('cpf', ''))

    def clean_cep(self):
        return _format_cep(self.cleaned_data.get('cep', ''))


class ClienteEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['cidade', 'estado', 'telefone', 'cep']
        widgets = {
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cidade'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UF', 'maxlength': 2}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000', 'maxlength': 9}),
        }
        labels = {
            'cidade': 'Cidade',
            'estado': 'Estado',
            'telefone': 'Telefone',
            'cep': 'CEP',
        }

    def clean_cep(self):
        return _format_cep(self.cleaned_data.get('cep', ''))


class PrestadorCadastroForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
        label='Nome completo',
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seuemail@exemplo.com'}),
        label='Email',
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
        label='Telefone',
    )
    cep = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000', 'maxlength': 9}),
        label='CEP',
    )
    category = forms.IntegerField(label='Categoria')
    experience = forms.IntegerField(min_value=0, label='Anos de experiência')
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control'}),
        label='Descrição dos serviços',
    )
    price = forms.DecimalField(min_value=0, max_digits=8, decimal_places=2, label='Preço por hora')

    def clean_cep(self):
        return _format_cep(self.cleaned_data.get('cep', ''))


class EditarPerfilPrestadorForm(forms.ModelForm):
    class Meta:
        model = PrestadorPerfil
        fields = ['bio', 'foto', 'especialidades', 'valor_hora', 'cidade', 'estado', 'cep', 'anos_experiencia', 'disponivel']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Fale sobre você e sua experiência...'}),
            'valor_hora': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'cidade': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Caçador'}),
            'estado': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: SC', 'maxlength': 2}),
            'cep': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: 89200-000', 'maxlength': 10}),
            'anos_experiencia': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'especialidades': forms.CheckboxSelectMultiple(attrs={'class': 'especialidade-checkbox'}),
            'disponivel': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'bio': 'Apresentação',
            'foto': 'Foto de Perfil',
            'especialidades': 'Especialidades',
            'valor_hora': 'Valor por Hora (R$)',
            'cidade': 'Cidade',
            'estado': 'Estado (sigla)',
            'cep': 'CEP',
            'anos_experiencia': 'Anos de Experiência',
            'disponivel': 'Disponível para novos serviços',
        }


class FiltroPrestadorForm(forms.Form):
    cidade = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ex: Caçador, SC'
        }),
        label='Cidade'
    )
    especialidade = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='Todas as especialidades',
        widget=forms.Select(attrs={'class': 'form-input'}),
        label='Especialidade'
    )
    valor_max = forms.DecimalField(
        required=False,
        max_digits=8, decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Máx R$/hora',
            'step': '0.01'
        }),
        label='Valor máximo por hora'
    )

    def __init__(self, *args, **kwargs):
        from .models import CategoriaServico
        super().__init__(*args, **kwargs)
        self.fields['especialidade'].queryset = CategoriaServico.objects.filter(ativo=True)
