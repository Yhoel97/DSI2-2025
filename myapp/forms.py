from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from .models import Valoracion




class LoginForm(AuthenticationForm):
    username = UsernameField(label='Usuario', widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'}))
    password = forms.CharField(label='Contraseña', strip=False, widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}))


class ValoracionForm(forms.ModelForm):
    """Formulario para crear/editar valoraciones de películas"""
    
    rating = forms.ChoiceField(
        choices=Valoracion.RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'rating-radio'}),
        label='Calificación'
    )
    
    resena = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Escribe tu reseña sobre esta película (opcional)...',
            'maxlength': 500
        }),
        label='Reseña (Opcional)'
    )
    
    class Meta:
        model = Valoracion
        fields = ['rating', 'resena']
        
    def __init__(self, *args, **kwargs):
        self.pelicula = kwargs.pop('pelicula', None)
        self.usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        
    def save(self, commit=True):
        valoracion = super().save(commit=False)
        if self.pelicula:
            valoracion.pelicula = self.pelicula
        if self.usuario:
            valoracion.usuario = self.usuario
        if commit:
            valoracion.save()
        return valoracion