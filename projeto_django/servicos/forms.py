from django import forms
from .models import Contrato, Avaliacao, PrestadorPerfil, UserProfile


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


class EditarPerfilPrestadorForm(forms.ModelForm):
    class Meta:
        model = PrestadorPerfil
        fields = ['bio', 'foto', 'especialidades', 'valor_hora', 'cidade', 'estado', 'anos_experiencia', 'disponivel']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Fale sobre você e sua experiência...'}),
            'valor_hora': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'cidade': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Caçador'}),
            'estado': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: SC', 'maxlength': 2}),
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
