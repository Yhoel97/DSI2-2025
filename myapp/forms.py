from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
import re


class LoginForm(AuthenticationForm):
    username = UsernameField(label='Usuario', widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'}))
    password = forms.CharField(label='Contraseña', strip=False, widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}))


class RegistroForm(UserCreationForm):
    """
    Formulario de registro de usuario con validaciones personalizadas
    Criterios de aceptación PBI-19:
    - Validar que el username no exista
    - Validar que el formato de email sea correcto  
    - Validar contraseña segura
    """
    
    username = forms.CharField(
        label='Nombre de usuario',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nombre de usuario',
            'autofocus': True
        }),
        help_text='Entre 3 y 150 caracteres. Solo letras, números y @/./+/-/_ permitidos.'
    )
    
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@correo.com'
        }),
        help_text='Ingresa un email válido. Este será único en el sistema.'
    )
    
    first_name = forms.CharField(
        label='Nombre',
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nombre (opcional)'
        })
    )
    
    last_name = forms.CharField(
        label='Apellido',
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu apellido (opcional)'
        })
    )
    
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 8 caracteres'
        }),
        help_text='Mínimo 8 caracteres, debe incluir letras y números.'
    )
    
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite tu contraseña'
        }),
        help_text='Ingresa la misma contraseña para verificación.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_username(self):
        """
        Criterio: Validar que el username no exista
        """
        username = self.cleaned_data.get('username')
        
        # Validar longitud mínima
        if len(username) < 3:
            raise forms.ValidationError('El nombre de usuario debe tener al menos 3 caracteres.')
        
        # Validar que no exista (case insensitive)
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso. Por favor elige otro.')
            
        return username

    def clean_email(self):
        """
        Criterio: Validar que el formato de email sea correcto
        """
        email = self.cleaned_data.get('email')
        
        # Validar formato básico (Django ya hace esto, pero agregamos validación extra)
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise forms.ValidationError('Por favor ingresa un email con formato válido (ejemplo@dominio.com).')
        
        # Validar que el email sea único
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este email ya está registrado. ¿Ya tienes una cuenta?')
            
        return email.lower()  # Normalizar a minúsculas

    def clean_password1(self):
        """
        Criterio: Validar contraseña segura
        """
        password = self.cleaned_data.get('password1')
        
        # Validar longitud mínima
        if len(password) < 8:
            raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres.')
        
        # Validar que contenga al menos una letra
        if not re.search(r'[a-zA-Z]', password):
            raise forms.ValidationError('La contraseña debe contener al menos una letra.')
        
        # Validar que contenga al menos un número
        if not re.search(r'\d', password):
            raise forms.ValidationError('La contraseña debe contener al menos un número.')
        
        # Validar que no sea solo números
        if password.isdigit():
            raise forms.ValidationError('La contraseña no puede ser solo números.')
        
        # Validar que no sea muy común
        common_passwords = ['12345678', 'password', 'qwerty123', 'abc123456']
        if password.lower() in common_passwords:
            raise forms.ValidationError('Esta contraseña es muy común. Por favor elige una más segura.')
            
        return password

    def save(self, commit=True):
        """
        Guardar usuario con datos adicionales
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        
        if commit:
            user.save()
        return user

    

