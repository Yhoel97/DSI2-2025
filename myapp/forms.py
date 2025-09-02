from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required




class LoginForm(AuthenticationForm):
    username = UsernameField(label='Usuario', widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'}))
    password = forms.CharField(label='Contraseña', strip=False, widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}))

    

