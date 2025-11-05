from io import BytesIO
from zipfile import ZipFile
import json
import random
from django.shortcuts import redirect
import string
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.urls import reverse
from DSI2025 import settings
from .forms import *
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from functools import wraps
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Pelicula, Reserva, Valoracion,CodigoDescuento
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from django.conf import settings
import os
from datetime import datetime
import qrcode
from reportlab.platypus import Image as RLImage
from PIL import Image as PILImage
from datetime import date
from django.db import models
from itertools import groupby
from django.shortcuts import render
from django.urls import reverse
from django.db.models import Q

from datetime import date
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt
from .models import Pelicula, Funcion, Reserva
from .decorators import admin_required
from django.http import HttpResponse
import pandas as pd
from reportlab.pdfgen import canvas
from .models import Pelicula, Venta
from django.db.models import Sum
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from .models import Venta
from django.db.models import Prefetch
from datetime import datetime
from .email import send_brevo_email   
from django.utils import timezone 
from datetime import date, datetime, timedelta
from itertools import groupby
import pytz

from .models import Pelicula, Funcion, Pago
from .utils.payment_simulator import simular_pago

# Diccionario de géneros con nombres completos
GENERO_CHOICES_DICT = {
    "AC": "Acción",
    "DR": "Drama",
    "CO": "Comedia",
    "TE": "Terror",
    "CF": "Ciencia Ficción",
    "RO": "Romance",
    "DO": "Documental",
    "AN": "Animacion",
    "FA": "Fantasía",  
}

@admin_required
@csrf_exempt
def peliculas(request):
    from datetime import date
    hoy = date.today()

    # 🔹 Filtrar películas según fecha de estreno
    peliculas_en_cartelera = Pelicula.objects.filter(
        Q(fecha_estreno__lte=hoy) | Q(fecha_estreno__isnull=True)
    ).order_by('-id')

    peliculas_proximas = Pelicula.objects.filter(
        fecha_estreno__gt=hoy
    ).order_by('fecha_estreno')

    # 🔹 Procesar búsqueda si existe
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        peliculas_en_cartelera = peliculas_en_cartelera.filter(
            Q(nombre__icontains=busqueda) | Q(director__icontains=busqueda)
        )
        peliculas_proximas = peliculas_proximas.filter(
            Q(nombre__icontains=busqueda) | Q(director__icontains=busqueda)
        )

    # 🔹 Procesar formulario (crear / editar / eliminar)
    if request.method == 'POST':
        accion = request.POST.get('accion')

        # --- CREAR ---
        if accion == 'crear':
            nombre = request.POST.get('nombre', '').strip()
            anio = request.POST.get('anio', '').strip()
            director = request.POST.get('director', '').strip()
            imagen_url = request.POST.get('imagen_url', '').strip()
            trailer_url = request.POST.get('trailer_url', '').strip()
            generos = request.POST.getlist('generos')
            salas = request.POST.getlist('salas')
            fecha_estreno = request.POST.get('fecha_estreno', '').strip()
            clasificacion = request.POST.get('clasificacion', 'APT')
            idioma = request.POST.get('idioma', 'ESP')

            errores = []
            if not nombre:
                errores.append('El nombre es obligatorio.')
            if Pelicula.objects.filter(nombre=nombre).exists():
                errores.append('Ya existe una película con ese nombre.')
            if not anio.isdigit() or int(anio) < 1900 or int(anio) > 2099:
                errores.append('El año debe estar entre 1900 y 2099.')
            if not director:
                errores.append('El director es obligatorio.')
            if not generos:
                errores.append('Debe seleccionar al menos un género.')
            if len(generos) > 3:
                errores.append('No puede seleccionar más de 3 géneros.')

            if errores:
                for e in errores:
                    messages.error(request, e)
            else:
                pelicula = Pelicula(
                    nombre=nombre,
                    anio=anio,
                    director=director,
                    imagen_url=imagen_url,
                    trailer_url=trailer_url,
                    generos=",".join(generos),
                    salas=",".join(salas),
                    fecha_estreno=fecha_estreno if fecha_estreno else None,
                    clasificacion=clasificacion,
                    idioma=idioma
                )
                pelicula.save()
                messages.success(request, f'Película "{nombre}" creada exitosamente.')
                return redirect('peliculas')

        # --- EDITAR ---
        elif accion == 'editar':
            nombre_original = request.POST.get('nombre_original', '').strip()
            try:
                pelicula = Pelicula.objects.get(nombre=nombre_original)
            except Pelicula.DoesNotExist:
                messages.error(request, 'No se encontró la película a editar.')
                return redirect('peliculas')

            pelicula.nombre = request.POST.get('nombre', '').strip()
            pelicula.anio = request.POST.get('anio', '').strip()
            pelicula.director = request.POST.get('director', '').strip()
            pelicula.imagen_url = request.POST.get('imagen_url', '').strip()
            pelicula.trailer_url = request.POST.get('trailer_url', '').strip()
            pelicula.generos = ",".join(request.POST.getlist('generos'))
            pelicula.salas = ",".join(request.POST.getlist('salas'))
            pelicula.fecha_estreno = request.POST.get('fecha_estreno') or None
            pelicula.clasificacion = request.POST.get('clasificacion', 'APT')
            pelicula.idioma = request.POST.get('idioma', 'ESP')
            pelicula.save()
            messages.success(request, f'Película "{pelicula.nombre}" actualizada correctamente.')
            return redirect('peliculas')

        # --- ELIMINAR ---
        elif accion == 'eliminar':
            nombre = request.POST.get('nombre', '').strip()
            try:
                Pelicula.objects.get(nombre=nombre).delete()
                messages.success(request, f'Película "{nombre}" eliminada correctamente.')
            except Pelicula.DoesNotExist:
                messages.error(request, 'No se encontró la película para eliminar.')
            return redirect('peliculas')

    # 🔹 Datos para el formulario y la tabla
    generos_choices = dict(Pelicula.GENERO_CHOICES)
    salas_disponibles = Pelicula.SALAS_DISPONIBLES  # ✅ ahora solo salas con formato

    pelicula_editar = None
    if 'editar' in request.GET:
        nombre = request.GET.get('editar')
        pelicula_editar = Pelicula.objects.filter(nombre=nombre).first()

    # 🔹 Convertir películas de cartelera con sus salas y formatos
    peliculas_con_pares = []
    for p in peliculas_en_cartelera:
        pares = p.get_salas_con_formato()  # ✅ devuelve (sala, formato)
        generos_nombres = [generos_choices.get(g, g) for g in p.get_generos_list()]
        peliculas_con_pares.append({
            'obj': p,
            'pares': pares,
            'generos_nombres': ", ".join(generos_nombres),
            'clasificacion': p.clasificacion,
            'idioma': p.idioma
        })

    # 🔹 Contexto para renderizar
    context = {
        'peliculas': peliculas_con_pares,          # En cartelera
        'peliculas_proximas': peliculas_proximas,  # Próximamente
        'GENERO_CHOICES_DICT': generos_choices,
        'SALAS_DISPONIBLES': salas_disponibles,
        'pelicula_editar': pelicula_editar,
        'busqueda': busqueda,
    }

    return render(request, 'peliculas.html', context)

#####################################################################

# Decorador personalizado para verificar si el usuario es admin
def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Redirigir a nuestro login personalizado
            return redirect('/accounts/login/')
        if not request.user.is_superuser:
            # Si no es superuser, redirigir al índice
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

#####################################################################################
def convertir_generos(codigos_generos):
    """Convierte códigos de género a nombres completos"""
    if not codigos_generos:
        return []
    return [GENERO_CHOICES_DICT.get(codigo.strip(), "Desconocido") 
            for codigo in codigos_generos.split(",")]

###############################################################################3

def index(request):
    from itertools import groupby
    from django.http import JsonResponse
    from django.db import models
    
    # ✅ Usar datetime.now() sin zona horaria
    ahora_naive = datetime.now()
    hoy = ahora_naive.date()
    
    # ✅ Obtener fecha seleccionada (si existe)
    fecha_seleccionada_str = request.GET.get('fecha')
    if fecha_seleccionada_str:
        try:
            fecha_seleccionada = datetime.strptime(fecha_seleccionada_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_seleccionada = hoy
    else:
        fecha_seleccionada = hoy

    # ✅ Nombres de meses en español
    nombres_meses_es = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    nombres_dias_es = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes', 
        'Wednesday': 'Miércoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    
    # ✅ Generar lista de 5 días (hoy + 4 días siguientes)
    dias_disponibles = []
    for i in range(5):
        dia = hoy + timedelta(days=i)
        dia_info = {
            'fecha': dia,
            'nombre_es': nombres_dias_es[dia.strftime('%A')],
            'formato_corto': dia.strftime('%d/%m')
        }
        dias_disponibles.append(dia_info)

    # ✅ Información de fecha seleccionada en español (FORMATO COMPLETO)
    nombre_dia_seleccionado = nombres_dias_es[fecha_seleccionada.strftime('%A')]
    nombre_mes_seleccionado = nombres_meses_es[fecha_seleccionada.month]
    
    # Formato: "Lunes 03 de Noviembre"
    fecha_formateada = f"{nombre_dia_seleccionado} {fecha_seleccionada.day:02d} de {nombre_mes_seleccionado}"

    # ✅ CARTELERA: Películas CON funciones activas en la fecha seleccionada
    # Ordenar por -pelicula__id para que las más recientes aparezcan primero
    funciones = (
        Funcion.objects.filter(
            activa=True,
            fecha_inicio__lte=fecha_seleccionada,
        )
        .select_related('pelicula')
        .order_by('-pelicula__id', 'horario')  # Orden descendente por ID de película
    )

    funciones_filtradas = []
    for funcion in funciones:
        fecha_fin_funcion = funcion.fecha_inicio + timedelta(weeks=funcion.semanas) - timedelta(days=1)
        
        if funcion.fecha_inicio <= fecha_seleccionada <= fecha_fin_funcion:
            if fecha_seleccionada == hoy:
                hora_funcion = datetime.strptime(funcion.horario, '%H:%M').time()
                datetime_funcion = datetime.combine(fecha_seleccionada, hora_funcion)
                
                margen = timedelta(minutes=10)
                if datetime_funcion > (ahora_naive - margen):
                    funciones_filtradas.append(funcion)
            else:
                funciones_filtradas.append(funcion)

    # ✅ Agrupar funciones por película (ordenadas por ID descendente)
    peliculas_cartelera = []
    peliculas_vistas = set()
    
    for funcion in funciones_filtradas:
        if funcion.pelicula.id not in peliculas_vistas:
            # Primera vez que vemos esta película
            pelicula = funcion.pelicula
            pelicula.funciones_del_dia = [f for f in funciones_filtradas if f.pelicula.id == pelicula.id]
            peliculas_cartelera.append(pelicula)
            peliculas_vistas.add(pelicula.id)

    # ✅ Enriquecer películas de cartelera
    for pelicula in peliculas_cartelera:
        pelicula.generos_list = pelicula.get_generos_list()
        pelicula.salas_con_formato = pelicula.get_salas_con_formato()
        pelicula.estrellas = (
            pelicula.get_rating_estrellas()
            if hasattr(pelicula, 'get_rating_estrellas')
            else {'llenas': 0, 'media': False}
        )

    # ✅ Si es request AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        peliculas_data = []
        for pelicula in peliculas_cartelera:
            # Obtener imagen URL
            imagen_url = ''
            if hasattr(pelicula, 'poster') and pelicula.poster:
                imagen_url = pelicula.poster.url
            elif hasattr(pelicula, 'imagen_url'):
                imagen_url = pelicula.imagen_url
            
            peliculas_data.append({
                'id': pelicula.id,
                'nombre': pelicula.nombre,
                'imagen_url': imagen_url,
                'generos': pelicula.generos_list if hasattr(pelicula, 'generos_list') else [],
                'director': pelicula.director if hasattr(pelicula, 'director') else 'Desconocido',
                'clasificacion': pelicula.get_clasificacion_display() if hasattr(pelicula, 'get_clasificacion_display') else 'N/A',
                'idioma': pelicula.get_idioma_display() if hasattr(pelicula, 'get_idioma_display') else 'N/A',
                'anio': pelicula.anio if hasattr(pelicula, 'anio') else '',
                'trailer_url': pelicula.trailer_url if hasattr(pelicula, 'trailer_url') else '#',
                'rating': pelicula.estrellas if hasattr(pelicula, 'estrellas') else {'llenas': 0, 'media': False},
                'rating_promedio': str(pelicula.get_rating_promedio()) if hasattr(pelicula, 'get_rating_promedio') else '0.0',
                'total_valoraciones': pelicula.get_total_valoraciones() if hasattr(pelicula, 'get_total_valoraciones') else 0,
                'funciones': [{
                    'horario': funcion.get_horario_display() if hasattr(funcion, 'get_horario_display') else funcion.horario,
                    'sala': str(funcion.sala),
                    'formato': funcion.get_formato_sala() if hasattr(funcion, 'get_formato_sala') else ''
                } for funcion in pelicula.funciones_del_dia]
            })
        
        return JsonResponse({
            'fecha_formateada': fecha_formateada,
            'es_hoy': fecha_seleccionada == hoy,
            'peliculas': peliculas_data,
            'total_peliculas': len(peliculas_cartelera)
        })

    # ✅ BASE DE DATOS (Solo Admin): TODAS las películas en cartelera
    peliculas_base_datos = []
    if request.user.is_authenticated and request.user.is_staff:
        peliculas_base_datos = Pelicula.objects.filter(
            models.Q(fecha_estreno__lte=hoy) | models.Q(fecha_estreno__isnull=True)
        ).order_by('-id')  # Más recientes primero
        
        # Enriquecer todas las películas de base de datos
        for pelicula in peliculas_base_datos:
            pelicula.generos_list = pelicula.get_generos_list()
            pelicula.salas_con_formato = pelicula.get_salas_con_formato()
            pelicula.estrellas = (
                pelicula.get_rating_estrellas()
                if hasattr(pelicula, 'get_rating_estrellas')
                else {'llenas': 0, 'media': False}
            )
            # Verificar si tiene funciones activas para la fecha seleccionada
            pelicula.tiene_funciones = Funcion.objects.filter(
                pelicula=pelicula,
                activa=True,
                fecha_inicio__lte=fecha_seleccionada
            ).exists()

    # ✅ PRÓXIMAMENTE: Películas con fecha de estreno futura
    peliculas_proximas = Pelicula.objects.filter(
        fecha_estreno__gt=hoy
    ).order_by('fecha_estreno')

    # Enriquecer películas próximas
    for pelicula in peliculas_proximas:
        pelicula.generos_list = pelicula.get_generos_list()

    es_admin = request.user.is_authenticated and request.user.is_staff

    return render(request, 'index.html', {
        'peliculas_base_datos': peliculas_base_datos,        # Admin: TODAS las películas
        'peliculas_proximas': peliculas_proximas,            # Próximamente
        'peliculas_cartelera': peliculas_cartelera,          # Cartelera activa
        'es_admin': es_admin,
        'dias_disponibles': dias_disponibles,
        'fecha_seleccionada': fecha_seleccionada,
        'fecha_formateada': fecha_formateada,
        'hoy': hoy,
        'nombres_dias_es': nombres_dias_es,
        'nombres_meses_es': nombres_meses_es,
    })

################################################################################

def my_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            if remember_me:
                request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            else:
                request.session.set_expiry(0)
                
            # Redirigir según el tipo de usuario - SIEMPRE basado en privilegios
            if user.is_superuser:
                return redirect('/peliculas/')
            else:
                return redirect('index')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'registration/login.html')


def my_logout(request):
    """Vista para cerrar sesión del usuario"""
    from django.contrib.auth import logout
    
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Has cerrado sesión exitosamente.')
        return redirect('index')
    elif request.method == 'GET':
        # Para enlaces directos, también permitimos logout via GET
        logout(request)
        messages.success(request, 'Has cerrado sesión exitosamente.')
        return redirect('index')
    
    return redirect('index')


def registro_usuario(request):
    """
    Vista para el registro de nuevos usuarios
    PBI-19: Implementa los criterios de aceptación para registro
    """
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            try:
                # Crear el usuario usando el formulario
                user = form.save()
                
                # Mensaje de éxito
                messages.success(
                    request, 
                    f'¡Bienvenido {user.username}! Tu cuenta ha sido creada exitosamente. '
                    'Ahora puedes iniciar sesión.'
                )
                
                # Redirigir al login después del registro exitoso
                return redirect('login')
                
            except Exception as e:
                messages.error(
                    request, 
                    f'Error al crear la cuenta: {str(e)}. Por favor intenta nuevamente.'
                )
        else:
            # Si el formulario tiene errores, se mostrarán automáticamente
            messages.error(
                request, 
                'Por favor corrige los errores en el formulario.'
            )
    else:
        # GET request - mostrar formulario vacío
        form = RegistroForm()
    
    return render(request, 'registration/registro.html', {
        'form': form,
        'title': 'Registro de Usuario'
    })


#######################################################################


PRECIOS_FORMATO = {
    '2D': 4.00,
    '3D': 6.00,
    'IMAX': 8.00
}

@csrf_exempt
def asientos(request, pelicula_id=None):
    pelicula = get_object_or_404(Pelicula, pk=pelicula_id) if pelicula_id else None
    if not pelicula:
        messages.error(request, "No se ha seleccionado ninguna película")
        return redirect('index')

    # Fecha seleccionada
    fecha_str = request.GET.get('fecha', '') or request.POST.get('fecha', '')
    ahora_naive = datetime.now()
    try:
        fecha_seleccionada = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else ahora_naive.date()
    except ValueError:
        fecha_seleccionada = ahora_naive.date()

    # Funciones vigentes
    funciones = Funcion.objects.filter(
        pelicula=pelicula,
        activa=True,
        fecha_inicio__lte=fecha_seleccionada
    ).order_by('horario')

    funciones_vigentes = []
    for funcion in funciones:
        fecha_fin_funcion = funcion.fecha_inicio + timedelta(weeks=funcion.semanas) - timedelta(days=1)
        if funcion.fecha_inicio <= fecha_seleccionada <= fecha_fin_funcion:
            if fecha_seleccionada == ahora_naive.date():
                hora_funcion = datetime.strptime(funcion.horario, '%H:%M').time()
                datetime_funcion = datetime.combine(fecha_seleccionada, hora_funcion)
                if datetime_funcion > (ahora_naive - timedelta(minutes=10)):
                    funciones_vigentes.append(funcion)
            else:
                funciones_vigentes.append(funcion)

    if not funciones_vigentes:
        messages.error(request, f"No hay funciones disponibles para esta película el {fecha_seleccionada.strftime('%d/%m/%Y')}")
        return redirect('index')

    # Función actual
    funcion_actual_id = request.POST.get('funcion_id') or request.GET.get('funcion_id')
    funcion_actual = None
    if funcion_actual_id:
        funcion_actual = next((f for f in funciones_vigentes if str(f.id) == str(funcion_actual_id)), None)
    if not funcion_actual and funciones_vigentes:
        funcion_actual = funciones_vigentes[0]

    # Asientos ocupados
    asientos_ocupados = []
    if funcion_actual:
        reservas_existentes = Reserva.objects.filter(
            pelicula=pelicula,
            sala=str(funcion_actual.sala),
            horario=funcion_actual.horario,
            fecha_funcion=fecha_seleccionada,
            estado__in=['RESERVADO', 'CONFIRMADO']
        )
        for r in reservas_existentes:
            asientos_ocupados.extend(r.get_asientos_list())

    # Datos de cálculo
    asientos_seleccionados = request.POST.getlist("asientos_list")
    cantidad_boletos = len(asientos_seleccionados)

    formato_actual = funcion_actual.get_formato_sala() if funcion_actual else '2D'
    precio_funcion_actual = PRECIOS_FORMATO.get(formato_actual, 4.00)

    # Cupón
    codigo_cupon = request.POST.get("codigo_cupon", "").strip()
    descuento_porcentaje = 0
    mensaje_cupon = ""
    if codigo_cupon:
        cupon = Cupon.objects.filter(codigo__iexact=codigo_cupon, activo=True).first()
        if cupon:
            descuento_porcentaje = cupon.porcentaje
            mensaje_cupon = f"Cupón aplicado: {descuento_porcentaje}%"
        else:
            mensaje_cupon = "Código inválido o inactivo"

    subtotal = cantidad_boletos * precio_funcion_actual
    descuento_monto = subtotal * (descuento_porcentaje / 100)
    total = subtotal - descuento_monto

    # --- AJAX: devolver JSON dinámico ---
    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "asientos": asientos_seleccionados,
            "cantidad_boletos": cantidad_boletos,
            "formato": formato_actual,
            "precio_boleto": precio_funcion_actual,
            "subtotal": subtotal,
            "descuento": descuento_porcentaje,
            "descuento_monto": descuento_monto,
            "total": total,
        })

    # --- Confirmar reserva ---
    if request.method == "POST" and request.POST.get("accion") == "reservar":
        nombre_cliente = request.POST.get("nombre_cliente", "").strip()
        apellido_cliente = request.POST.get("apellido_cliente", "").strip()
        email = request.POST.get("email", "").strip()
        funcion_id = request.POST.get("funcion_id")

        # Datos de pago
        numero_tarjeta = request.POST.get("numero_tarjeta", "").strip().replace(" ", "")
        nombre_titular = request.POST.get("nombre_titular", "").strip()
        fecha_expiracion = request.POST.get("fecha_expiracion", "").strip()
        cvv = request.POST.get("cvv", "").strip()

        errores = []
        if not nombre_cliente: errores.append("El nombre es obligatorio")
        if not apellido_cliente: errores.append("El apellido es obligatorio")
        if not email or "@" not in email: errores.append("Ingrese un email válido")
        if not funcion_id: errores.append("Seleccione una función")
        if cantidad_boletos == 0: errores.append("Seleccione al menos un asiento")
        
        # Validaciones de pago
        if not numero_tarjeta: errores.append("El número de tarjeta es obligatorio")
        if not nombre_titular: errores.append("El nombre del titular es obligatorio")
        if not fecha_expiracion: errores.append("La fecha de expiración es obligatoria")
        if not cvv: errores.append("El CVV es obligatorio")

        if not errores:
            try:
                funcion = get_object_or_404(Funcion, id=funcion_id)
                formato_funcion = funcion.get_formato_sala()
                precio_por_boleto = PRECIOS_FORMATO.get(formato_funcion, 4.00)

                subtotal = cantidad_boletos * precio_por_boleto
                descuento_monto = subtotal * (descuento_porcentaje / 100)
                precio_total = subtotal - descuento_monto

                # Procesar pago simulado
                resultado_pago = simular_pago(
                    numero_tarjeta=numero_tarjeta,
                    nombre_titular=nombre_titular,
                    fecha_expiracion=fecha_expiracion,
                    cvv=cvv,
                    monto=float(precio_total)
                )

                # Crear registro de pago pendiente
                pago = Pago(
                    reserva=None,  # Se asignará después si el pago es exitoso
                    monto=precio_total,
                    metodo_pago="TARJETA",
                    estado_pago="PENDIENTE",
                    numero_transaccion=resultado_pago.get("numero_transaccion", ""),
                    detalles_pago={
                        "numero_tarjeta_enmascarado": resultado_pago.get("numero_tarjeta_enmascarado", ""),
                        "nombre_titular": nombre_titular,
                        "tipo_tarjeta": resultado_pago.get("tipo_tarjeta", ""),
                    }
                )
                pago.save()

                if resultado_pago["exitoso"]:
                    # Pago exitoso: actualizar estado y crear reserva
                    pago.estado_pago = "APROBADO"
                    pago.save()

                    # Crear reserva
                    reserva = Reserva(
                        pelicula=pelicula,
                        nombre_cliente=nombre_cliente,
                        apellido_cliente=apellido_cliente,
                        email=email,
                        formato=formato_funcion,
                        sala=str(funcion.sala),
                        horario=funcion.horario,
                        fecha_funcion=fecha_seleccionada,
                        asientos=",".join(asientos_seleccionados),
                        cantidad_boletos=cantidad_boletos,
                        precio_total=precio_total,
                        estado="RESERVADO",
                        usuario=request.user if request.user.is_authenticated else None,
                        pago_completado=True,
                        fecha_pago=timezone.now()
                    )
                    reserva.codigo_reserva = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
                    reserva.save()

                    # Asociar pago con reserva
                    pago.reserva = reserva
                    pago.save()

                    # Registrar venta
                    Venta.objects.create(
                        pelicula=reserva.pelicula,
                        sala=reserva.sala,
                        fecha=fecha_seleccionada,
                        cantidad_boletos=reserva.cantidad_boletos,
                        total_venta=reserva.precio_total
                    )

                    # PDF y correo
                    pdf_buffer = generar_pdf_reserva(reserva)
                    subject = f"Confirmación de Reserva - Código {reserva.codigo_reserva}"
                    body = (
                        f"Hola {reserva.nombre_cliente},<br><br>"
                        f"Tu reserva para la película '{reserva.pelicula.nombre}' ha sido confirmada.<br>"
                        f"Código de reserva: {reserva.codigo_reserva}<br>"
                        f"Fecha: {fecha_seleccionada.strftime('%d/%m/%Y')}<br>"
                        f"Horario: {funcion.get_horario_display()}<br>"
                        f"Sala: {funcion.sala}<br>"
                        f"Formato: {formato_funcion}<br>"
                        f"Asientos: {','.join(asientos_seleccionados)}<br>"
                        f"Subtotal: ${subtotal:.2f}<br>"
                        f"Descuento: -${descuento_monto:.2f}<br>"
                        f"Total: ${precio_total:.2f}<br>"
                        f"Transacción: {pago.numero_transaccion}<br><br>"
                        "Adjunto encontrarás tu ticket en formato PDF.<br><br>"
                        "¡Gracias por elegir CineDot!"
                    )
                    send_brevo_email(
                        to_emails=[reserva.email],
                        subject=subject,
                        html_content=body,
                        attachments=[(f"ticket_{reserva.codigo_reserva}.pdf", pdf_buffer.getvalue(), "application/pdf")]
                    )

                    request.session["codigo_reserva"] = reserva.codigo_reserva
                    messages.success(request, f"¡Pago y reserva exitosos! Código: {reserva.codigo_reserva}")
                    return redirect(f"{reverse('asientos', args=[pelicula.id])}?fecha={fecha_seleccionada.strftime('%Y-%m-%d')}")
                else:
                    # Pago rechazado
                    pago.estado_pago = "RECHAZADO"
                    pago.detalles_pago["mensaje_error"] = resultado_pago.get("mensaje", "Pago rechazado")
                    pago.save()
                    
                    messages.error(request, f"Error en el pago: {resultado_pago.get('mensaje', 'Pago rechazado')}. Por favor, intente nuevamente.")
            except Exception as e:
                messages.error(request, f"Error al procesar la transacción: {str(e)}")
        else:
            for error in errores:
                messages.error(request, error)

    # --- Render normal (GET inicial o POST sin reservar) ---
    funciones_con_precios = []
    for funcion in funciones_vigentes:
        formato = funcion.get_formato_sala()
        precio = PRECIOS_FORMATO.get(formato, 4.00)
        funciones_con_precios.append({
            "funcion": funcion,
            "formato": formato,
            "precio": precio
        })

    context = {
        "pelicula": pelicula,
        "asientos_ocupados": asientos_ocupados,
        "funciones_vigentes": funciones_vigentes,
        "funciones_con_precios": funciones_con_precios,
        "funcion_actual": funcion_actual,
        "fecha_seleccionada": fecha_seleccionada,
        "codigo_reserva": request.session.get("codigo_reserva"),
        "precio_funcion_actual": precio_funcion_actual,
        "formato_actual": formato_actual,
        "asientos_seleccionados": asientos_seleccionados,
        "cantidad_boletos": cantidad_boletos,
        "subtotal": subtotal,
        "descuento_porcentaje": descuento_porcentaje,
        "descuento_monto": descuento_monto,
        "total": total,
        "mensaje_cupon": mensaje_cupon,
        "nombre_cliente": request.POST.get("nombre_cliente", ""),
        "apellido_cliente": request.POST.get("apellido_cliente", ""),
        "email": request.POST.get("email", ""),
        "codigo_cupon": codigo_cupon,
    }
    return render(request, "asientos.html", context)
       


#################################################################
#################################################################
@csrf_exempt
@require_POST
def aplicar_descuento_ajax(request):
    """
    Función que valida un código de descuento y guarda el porcentaje en la sesión.
    Responde con JSON.
    """
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().upper()
        
        if not codigo:
            return JsonResponse({'success': False, 'mensaje': 'Ingrese un código de descuento.'})

        try:
            cupon = CodigoDescuento.objects.get(codigo=codigo, estado=True)

            # Aplicacion de el descuento y guardarlo en la sesión
            descuento = cupon.porcentaje
            
            descuento = float(cupon.porcentaje or 0)
            request.session['descuento_porcentaje'] = descuento
            
            mensaje = f'Cupón "{codigo}" aplicado: ¡{descuento}% de descuento!'
            request.session['mensaje_cupon'] = mensaje
            
            return JsonResponse({'success': True, 'descuento_porcentaje': descuento, 'mensaje': mensaje})

        except CodigoDescuento.DoesNotExist:
            return JsonResponse({'success': False, 'mensaje': 'Código no válido o inactivo.'})

        except Exception as e:
            return JsonResponse({'success': False, 'mensaje': f'Error interno: {str(e)}'})

    return JsonResponse({'success': False, 'mensaje': 'Método no permitido.'})
#################################################################
#################################################################
def registrar_cupon(request):
  
    if request.method == 'POST':
        
        form = CodigoDescuentoForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('registrar_cupon') 
    
    else:
        form = CodigoDescuentoForm()

    cupones_registrados = CodigoDescuento.objects.all().order_by('-id')

    contexto = {
        'form': form,
        'cupones': cupones_registrados 
    }

    return render(request, 'registrar_cupon.html', contexto)
    
def eliminar_cupon(request, pk):
   
    cupon = get_object_or_404(CodigoDescuento, pk=pk)
    cupon.delete() 
    return redirect('registrar_cupon')

def modificar_cupon(request, pk):
    cupon = get_object_or_404(CodigoDescuento, pk=pk)
    
    if request.method == 'POST':
        form = CodigoDescuentoForm(request.POST, instance=cupon)
        if form.is_valid():
            form.save()
            return redirect('registrar_cupon') 
    else:
        form = CodigoDescuentoForm(instance=cupon)
        
    cupones_registrados = CodigoDescuento.objects.all().order_by('-id')
    
    contexto = {
        'form': form,
        'cupones': cupones_registrados,
        'es_edicion': True, # Sirve para identificar si se esta modificandi
        'cupon_id': pk
    }
    
    return render(request, 'registrar_cupon.html', contexto)

##################################################################################
##################################################################################
@csrf_exempt
def administrar_salas(request):
    peliculas = Pelicula.objects.all()
    pelicula_id = request.GET.get('pelicula')
    combo = request.GET.get('combo')
    pelicula = Pelicula.objects.filter(id=pelicula_id).first() if pelicula_id else None
    combinaciones = []
    asientos_ocupados = []

    if pelicula:
        horarios = pelicula.get_horarios_list()
        salas = pelicula.get_salas_list()
        combinaciones = [f"{h} - {s}" for h, s in zip(horarios, salas)]

        if combo:
            try:
                horario_sel, sala_sel = combo.split(" - ", 1)
                reservas = Reserva.objects.filter(
                    pelicula=pelicula,
                    horario=horario_sel.strip(),
                    sala=sala_sel.strip(),
                    estado__in=['RESERVADO', 'CONFIRMADO']
                )
                for r in reservas:
                    asientos_ocupados.extend(r.get_asientos_list())
            except ValueError:
                pass

        # Restablecer todos los asientos
        if request.method == 'POST' and request.POST.get('restablecer') == 'true':
            Reserva.objects.filter(
                pelicula=pelicula,
                horario=horario_sel.strip(),
                sala=sala_sel.strip(),
                estado__in=['RESERVADO', 'CONFIRMADO']
            ).delete()
            return JsonResponse({'success': True})

        # Eliminar asiento individual
        if request.method == 'POST' and request.POST.get('eliminar_asiento'):
            asiento = request.POST.get('eliminar_asiento')
            for r in reservas:
                asientos = r.get_asientos_list()
                if asiento in asientos:
                    asientos.remove(asiento)
                    if asientos:
                        r.asientos = ",".join(asientos)
                        r.save()
                    else:
                        r.delete()
                    return JsonResponse({'success': True})
            return JsonResponse({'success': False, 'error': 'Asiento no encontrado'})

    context = {
        'peliculas': peliculas,
        'pelicula': pelicula,
        'combinaciones': combinaciones,
        'combo_actual': combo,
        'asientos_ocupados': asientos_ocupados,
    }
    return render(request, 'administrar_salas.html', context)

################################################################


def generar_pdf_reserva(reserva):
    buffer = BytesIO()
    
    # Obtener fecha y hora actual del sistema
    ahora = datetime.now()
    fecha_emision = ahora.strftime('%d/%m/%Y %H:%M:%S')

    # Configurar el documento
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=72)
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Crear estilos personalizados
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=20,
        leading=24,
        spaceAfter=20,
        alignment=1,
        textColor=colors.HexColor('#2c3e50')
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        spaceAfter=12,
        alignment=1,
        textColor=colors.HexColor('#3498db')
    )
    
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=12,
        leading=15,
        spaceAfter=8
    )
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        textColor=colors.grey,
        alignment=1
    )
    
    # Contenido del PDF
    elements = []
    
    # Logo
    logo_path = os.path.abspath(os.path.join(settings.BASE_DIR, 'myapp', 'static', 'imagenes', 'cine.png'))
    if os.path.exists(logo_path):
        pil_logo = PILImage.open(logo_path)
        original_width, original_height = pil_logo.size

        # Convertir a pulgadas
        width_inch = original_width / 96
        height_inch = original_height / 96

        # Escalar a la mitad
        scale = 0.5
        final_width = width_inch * inch * scale
        final_height = height_inch * inch * scale

        # Insertar logo sin margen superior
        logo = Image(logo_path, width=final_width, height=final_height)
        elements.append(logo)

        # Espacio opcional debajo del logo
        elements.append(Spacer(1, 0.1 * inch))



    # Título
    elements.append(Paragraph("CineDot", title_style))
    elements.append(Paragraph("Ticket de Reserva", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Información de emisión
    emision_data = [
        [Paragraph("<b>Fecha de emisión:</b>", info_style), 
         Paragraph(fecha_emision, info_style)]
    ]
    
    emision_table = Table(emision_data, colWidths=[1.5*inch, 4*inch])
    emision_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    elements.append(emision_table)
    
    # Información del cliente
    cliente_data = [
        [Paragraph("<b>Cliente:</b>", info_style), 
         Paragraph(f"{reserva.nombre_cliente} {reserva.apellido_cliente}", info_style)],
        [Paragraph("<b>Email:</b>", info_style), 
         Paragraph(reserva.email, info_style)],
    ]
    
    cliente_table = Table(cliente_data, colWidths=[1.5*inch, 4*inch])
    cliente_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(cliente_table)
    elements.append(Spacer(1, 20))
    
    # Información de la reserva
    reserva_data = [
        [Paragraph("<b>Código de reserva:</b>", info_style), 
         Paragraph(reserva.codigo_reserva, info_style)],
        [Paragraph("<b>Fecha de reserva:</b>", info_style), 
         Paragraph(reserva.fecha_reserva.strftime('%d/%m/%Y %H:%M'), info_style)],
        [Paragraph("<b>Película:</b>", info_style), 
         Paragraph(reserva.pelicula.nombre, info_style)],
        [Paragraph("<b>Formato:</b>", info_style), 
         Paragraph(reserva.get_formato_display(), info_style)],
        [Paragraph("<b>Sala:</b>", info_style), 
         Paragraph(reserva.sala, info_style)],
        [Paragraph("<b>Horario:</b>", info_style), 
         Paragraph(reserva.horario, info_style)],
        [Paragraph("<b>Asientos:</b>", info_style), 
         Paragraph(reserva.asientos, info_style)],
        [Paragraph("<b>Cantidad de boletos:</b>", info_style), 
         Paragraph(str(reserva.cantidad_boletos), info_style)],
        [Paragraph("<b>Total:</b>", info_style), 
         Paragraph(f"${reserva.precio_total:.2f}", info_style)],
    ]
    
    reserva_table = Table(reserva_data, colWidths=[1.5*inch, 4*inch])
    reserva_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-2), 1, colors.lightgrey),
        ('GRID', (0,-1), (-1,-1), 1, colors.HexColor('#3498db')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#f8f9fa')),
    ]))
    elements.append(reserva_table)
    elements.append(Spacer(1, 30))
        # Código QR
    qr_image = generar_qr(reserva)
    elements.append(Paragraph("Escanee este código para validar su ticket", info_style))
    elements.append(qr_image)
    elements.append(Spacer(1, 20))
    
    # Mensaje de agradecimiento
    elements.append(Paragraph("Presente este ticket en la entrada del cine", footer_style))
    elements.append(Paragraph("¡Gracias por su preferencia!", footer_style))


    
    # Construir el PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer






def descargar_ticket(request, codigo_reserva):
    reserva = get_object_or_404(Reserva, codigo_reserva=codigo_reserva)
    pdf_buffer = generar_pdf_reserva(reserva)

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket_{reserva.codigo_reserva}.pdf"'
    return response
##########################################################################


def generar_qr(reserva):
    url = f"https://system-design.onrender.com/validaQR/{reserva.codigo_reserva}/"
    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    buffer.seek(0)
    return RLImage(buffer, width=1.5*inch, height=1.5*inch)
########################################################################################

def validaQR(request, codigo_reserva):
    reserva = get_object_or_404(Reserva, codigo_reserva=codigo_reserva)

    if reserva.usado:
        mensaje = "❌ Ticket inválido: ya fue utilizado."
        valido = False
    else:
        reserva.usado = True
        reserva.save()
        mensaje = "✅ Ticket válido: bienvenido al cine."
        valido = True

    return render(request, "validaQR.html", {
        "mensaje": mensaje,
        "valido": valido,
        "reserva": reserva,
        "pelicula": reserva.pelicula
    })

################################################################################
# VALORACIONES Y RESEÑAS - PBI-24
################################################################################

def pelicula_detalle(request, pelicula_id):
    """Vista para mostrar detalle de película con valoraciones"""
    pelicula = get_object_or_404(Pelicula, id=pelicula_id)
    
    # Obtener todas las valoraciones de la película
    valoraciones_list = pelicula.valoraciones.all().order_by('-fecha_creacion')
    
    # Paginación de valoraciones
    paginator = Paginator(valoraciones_list, 5)  # 5 valoraciones por página
    page_number = request.GET.get('page')
    valoraciones = paginator.get_page(page_number)
    
    # Verificar si el usuario ya ha valorado esta película
    valoracion_usuario = None
    if request.user.is_authenticated:
        try:
            valoracion_usuario = Valoracion.objects.get(pelicula=pelicula, usuario=request.user)
        except Valoracion.DoesNotExist:
            valoracion_usuario = None
    
    # Convertir géneros para mostrar nombres completos
    pelicula.get_generos_list = convertir_generos(pelicula.generos)
    
    context = {
        'pelicula': pelicula,
        'valoraciones': valoraciones,
        'valoracion_usuario': valoracion_usuario,
        'puede_valorar': request.user.is_authenticated and not valoracion_usuario,
    }
    
    return render(request, 'pelicula_detalle.html', context)


@login_required
def crear_valoracion(request, pelicula_id):
    """Vista para crear o actualizar valoración de una película"""
    pelicula = get_object_or_404(Pelicula, id=pelicula_id)
    
    # Verificar si ya existe una valoración del usuario
    try:
        valoracion_existente = Valoracion.objects.get(pelicula=pelicula, usuario=request.user)
    except Valoracion.DoesNotExist:
        valoracion_existente = None
    
    if request.method == 'POST':
        form = ValoracionForm(
            request.POST, 
            instance=valoracion_existente,
            pelicula=pelicula, 
            usuario=request.user
        )
        
        if form.is_valid():
            valoracion = form.save()
            if valoracion_existente:
                messages.success(request, '¡Tu valoración ha sido actualizada!')
            else:
                messages.success(request, '¡Gracias por tu valoración!')
            
            return redirect('pelicula_detalle', pelicula_id=pelicula.id)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ValoracionForm(
            instance=valoracion_existente,
            pelicula=pelicula, 
            usuario=request.user
        )
    
    context = {
        'form': form,
        'pelicula': pelicula,
        'valoracion_existente': valoracion_existente,
    }
    
    return render(request, 'crear_valoracion.html', context)


@login_required  
def eliminar_valoracion(request, pelicula_id):
    """Vista para eliminar valoración propia"""
    pelicula = get_object_or_404(Pelicula, id=pelicula_id)
    
    try:
        valoracion = Valoracion.objects.get(pelicula=pelicula, usuario=request.user)
        valoracion.delete()
        messages.success(request, 'Tu valoración ha sido eliminada.')
    except Valoracion.DoesNotExist:
        messages.error(request, 'No se encontró tu valoración.')
    
    return redirect('pelicula_detalle', pelicula_id=pelicula.id)

###############################################################################


def filtrar_peliculas(request):
    """
    Muestra SOLO películas con funciones activas vigentes HOY
    (misma lógica que index para cartelera)
    """
    from django.db.models import Q
    
    genero = request.GET.get('genero', '').strip()
    clasificacion = request.GET.get('clasificacion', '').strip()
    idioma = request.GET.get('idioma', '').strip()

    # ✅ Usar datetime.now() sin zona horaria
    ahora_naive = datetime.now()
    hoy = ahora_naive.date()

    # ✅ CARTELERA: Películas CON funciones activas vigentes HOY
    funciones = (
        Funcion.objects.filter(
            activa=True,
            fecha_inicio__lte=hoy,
        )
        .select_related('pelicula')
        .order_by('-pelicula__id', 'horario')
    )

    funciones_filtradas = []
    for funcion in funciones:
        fecha_fin_funcion = funcion.fecha_inicio + timedelta(weeks=funcion.semanas) - timedelta(days=1)
        
        # Verificar que la función esté en el rango de fechas
        if funcion.fecha_inicio <= hoy <= fecha_fin_funcion:
            # Verificar que no haya pasado (margen de 10 minutos)
            hora_funcion = datetime.strptime(funcion.horario, '%H:%M').time()
            datetime_funcion = datetime.combine(hoy, hora_funcion)
            
            margen = timedelta(minutes=10)
            if datetime_funcion > (ahora_naive - margen):
                funciones_filtradas.append(funcion)

    # ✅ Agrupar funciones por película
    peliculas_dict = {}
    for funcion in funciones_filtradas:
        pelicula_id = funcion.pelicula.id
        if pelicula_id not in peliculas_dict:
            peliculas_dict[pelicula_id] = {
                'pelicula': funcion.pelicula,
                'funciones': []
            }
        peliculas_dict[pelicula_id]['funciones'].append(funcion)

    # ✅ Convertir a lista de películas
    peliculas_base = [item['pelicula'] for item in peliculas_dict.values()]

    # 🔹 Aplicar filtros del formulario
    peliculas_filtradas = []
    for pelicula in peliculas_base:
        cumple_filtros = True
        
        if genero and genero not in pelicula.generos:
            cumple_filtros = False
        if clasificacion and pelicula.clasificacion != clasificacion:
            cumple_filtros = False
        if idioma and pelicula.idioma != idioma:
            cumple_filtros = False
            
        if cumple_filtros:
            # Agregar funciones del día a la película
            pelicula.funciones_del_dia = peliculas_dict[pelicula.id]['funciones']
            peliculas_filtradas.append(pelicula)

    # 🔹 Enriquecer películas con información adicional
    for pelicula in peliculas_filtradas:
        pelicula.generos_list = pelicula.get_generos_list()
        pelicula.salas_con_formato = pelicula.get_salas_con_formato()

    context = {
        'peliculas': peliculas_filtradas,
        'genero': genero,
        'clasificacion': clasificacion,
        'idioma': idioma,
        'GENERO_CHOICES': Pelicula.GENERO_CHOICES,
    }

    return render(request, 'filtrar.html', context)


###################################################################################

def horarios_por_pelicula(request):
    """
    Muestra SOLO películas con funciones activas vigentes HOY
    con todos sus horarios y salas disponibles
    (misma lógica que index para cartelera)
    """
    # ✅ Usar datetime.now() sin zona horaria
    ahora_naive = datetime.now()
    hoy = ahora_naive.date()

    # ✅ CARTELERA: Películas CON funciones activas vigentes HOY
    funciones = (
        Funcion.objects.filter(
            activa=True,
            fecha_inicio__lte=hoy,
        )
        .select_related('pelicula')
        .order_by('-pelicula__id', 'horario')
    )

    funciones_filtradas = []
    for funcion in funciones:
        fecha_fin_funcion = funcion.fecha_inicio + timedelta(weeks=funcion.semanas) - timedelta(days=1)
        
        # Verificar que la función esté en el rango de fechas
        if funcion.fecha_inicio <= hoy <= fecha_fin_funcion:
            # Verificar que no haya pasado (margen de 10 minutos)
            hora_funcion = datetime.strptime(funcion.horario, '%H:%M').time()
            datetime_funcion = datetime.combine(hoy, hora_funcion)
            
            margen = timedelta(minutes=10)
            if datetime_funcion > (ahora_naive - margen):
                funciones_filtradas.append(funcion)

    # ✅ Agrupar funciones por película (ordenadas por ID descendente)
    peliculas_cartelera = []
    peliculas_vistas = set()
    
    for funcion in funciones_filtradas:
        if funcion.pelicula.id not in peliculas_vistas:
            # Primera vez que vemos esta película
            pelicula = funcion.pelicula
            pelicula.funciones_del_dia = [f for f in funciones_filtradas if f.pelicula.id == pelicula.id]
            peliculas_cartelera.append(pelicula)
            peliculas_vistas.add(pelicula.id)

    # ✅ Enriquecer películas
    for pelicula in peliculas_cartelera:
        pelicula.generos_list = pelicula.get_generos_list()
        pelicula.salas_con_formato = pelicula.get_salas_con_formato()

    context = {
        'peliculas': peliculas_cartelera,
        'fecha': hoy,
    }

    return render(request, 'horarios.html', context)


##################################################################
##################################################################
# Zona horaria de El Salvador
TZ_ES = pytz.timezone("America/El_Salvador")

# Distancia mínima entre funciones en minutos (2h30m)
DISTANCIA_MINIMA_MIN = 150

def _ahora_es():
    return datetime.now(TZ_ES)

def parse_hora(hhmm: str):
    """Convierte 'HH:MM' a objeto datetime.time"""
    h, m = hhmm.split(":")
    return datetime(2000, 1, 1, int(h), int(m)).time()

def _minutos_entre(hora_a, hora_b):
    a = datetime(2000, 1, 1, hora_a.hour, hora_a.minute)
    b = datetime(2000, 1, 1, hora_b.hour, hora_b.minute)
    return abs(int((b - a).total_seconds() // 60))

def hay_conflicto_distancia(hora, existentes):
    """Valida si 'hora' incumple la distancia mínima con 'existentes'"""
    for h in existentes:
        if _minutos_entre(h, hora) < DISTANCIA_MINIMA_MIN:
            return True
    return False

@csrf_exempt
def administrar_funciones(request):
    hoy_es = _ahora_es().date()

    # ✅ Extraer TODAS las películas de la BD (ordenadas: última agregada primero)
    peliculas = Pelicula.objects.all().order_by('-id')

    # ✅ Enriquecer cada película con sus datos asociados
    generos_choices = dict(Pelicula.GENERO_CHOICES)
    peliculas_con_pares = []
    
    for p in peliculas:
        pares = p.get_salas_con_formato()
        generos_nombres = [generos_choices.get(g, g) for g in p.get_generos_list()]
        peliculas_con_pares.append({
            'obj': p,
            'pares': pares,
            'generos_nombres': ", ".join(generos_nombres),
            'clasificacion': p.clasificacion,
            'idioma': p.idioma
        })

    # ✅ Para el dropdown de películas
    for pelicula in peliculas:
        pelicula.generos_list = pelicula.get_generos_list()
        pelicula.salas_con_formato = pelicula.get_salas_con_formato()
        pelicula.estrellas = (
            pelicula.get_rating_estrellas()
            if hasattr(pelicula, 'get_rating_estrellas')
            else {'llenas': 0, 'media': False}
        )

    # ✅ CORRECCIÓN CRÍTICA: Ordenar por pelicula__id para que regroup funcione
    # Funciones actuales: activas Y fecha_inicio >= hoy
    funciones_actuales = Funcion.objects.filter(
        activa=True,
        fecha_inicio__gte=hoy_es
    ).select_related('pelicula').order_by('pelicula__id', 'horario')

    # Funciones pasadas: inactivas O fecha_inicio < hoy
    funciones_pasadas = Funcion.objects.filter(
        models.Q(activa=False) | models.Q(fecha_inicio__lt=hoy_es)
    ).select_related('pelicula').order_by('pelicula__id', 'horario')

    funcion_editar = None

    if request.method == "POST":
        accion = request.POST.get("accion")

        # --- AGREGAR NUEVA FUNCIÓN CON MÚLTIPLES HORARIOS ---
        if accion == "agregar":
            pelicula_id = request.POST.get("pelicula")
            fecha_inicio_str = request.POST.get("fecha_inicio")
            semanas = request.POST.get("semanas", 1)
            
            # Obtener arrays de horarios y salas
            horarios = request.POST.getlist('horario[]')
            salas = request.POST.getlist('sala[]')

            try:
                # Validar datos requeridos
                if not all([pelicula_id, fecha_inicio_str]):
                    messages.error(request, "❌ Película y fecha son obligatorios.")
                    return redirect("administrar_funciones")

                if not horarios or not salas:
                    messages.error(request, "❌ Debes agregar al menos un horario y sala.")
                    return redirect("administrar_funciones")

                # Obtener objetos relacionados
                pelicula = Pelicula.objects.get(id=pelicula_id)
                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()

                # Validar que la fecha no sea pasada
                if fecha_inicio < hoy_es:
                    messages.error(request, "❌ No puedes crear funciones con fecha pasada.")
                    return redirect("administrar_funciones")

                funciones_creadas = 0
                errores = []

                # Procesar cada par horario-sala
                for i, (horario, sala_nombre) in enumerate(zip(horarios, salas)):
                    if not horario or not sala_nombre:
                        continue  # Saltar campos vacíos

                    try:
                        # Validar que la sala exista en las salas disponibles de la película
                        salas_pelicula = [sala_tuple[0] for sala_tuple in pelicula.get_salas_con_formato()]
                        if sala_nombre not in salas_pelicula:
                            errores.append(f"La sala '{sala_nombre}' no está disponible para esta película")
                            continue

                        # Validar conflicto de horarios en la misma sala y fecha
                        funciones_existentes = Funcion.objects.filter(
                            sala__icontains=sala_nombre,  # Buscar por nombre de sala en string
                            fecha_inicio=fecha_inicio,
                            activa=True
                        )
                        
                        horarios_existentes = [parse_hora(func.horario) for func in funciones_existentes]
                        nuevo_horario = parse_hora(horario)

                        if hay_conflicto_distancia(nuevo_horario, horarios_existentes):
                            errores.append(f"Horario {horario} en {sala_nombre}: conflicto con funciones existentes")
                            continue

                        # Crear la nueva función - usar sala como string
                        nueva_funcion = Funcion(
                            pelicula=pelicula,
                            sala=sala_nombre,  # Guardar como string
                            horario=horario,
                            fecha_inicio=fecha_inicio,
                            semanas=int(semanas),
                            activa=True
                        )
                        nueva_funcion.save()
                        funciones_creadas += 1

                    except Exception as e:
                        errores.append(f"Error en horario {horario}: {str(e)}")

                # Mostrar resultados
                if funciones_creadas > 0:
                    messages.success(request, f"✅ {funciones_creadas} función(es) agregada(s) para {pelicula.nombre}")
                
                if errores:
                    for error in errores:
                        messages.warning(request, f"⚠️ {error}")
                
                # Recargar los QuerySets después de agregar
                funciones_actuales = Funcion.objects.filter(
                    activa=True,
                    fecha_inicio__gte=hoy_es
                ).select_related('pelicula').order_by('pelicula__id', 'horario')
                
                funciones_pasadas = Funcion.objects.filter(
                    models.Q(activa=False) | models.Q(fecha_inicio__lt=hoy_es)
                ).select_related('pelicula').order_by('pelicula__id', 'horario')
                
            except Pelicula.DoesNotExist:
                messages.error(request, "❌ La película seleccionada no existe.")
            except ValueError as e:
                messages.error(request, f"❌ Error en el formato de fecha: {str(e)}")
            except Exception as e:
                messages.error(request, f"❌ Error al agregar funciones: {str(e)}")

        # --- REACTIVAR FUNCIÓN ---
        elif accion == "reactivar":
            funcion_id = request.POST.get("funcion_id")
            if funcion_id:
                try:
                    funcion = Funcion.objects.get(id=funcion_id)
                    # CORRECCIÓN: Al reactivar, también actualizar fecha_inicio si es pasada
                    if funcion.fecha_inicio < hoy_es:
                        funcion.fecha_inicio = hoy_es
                    
                    # Reactivar la función
                    funcion.activa = True
                    funcion.fecha_eliminacion = None
                    funcion.save()
                    
                    messages.success(request, f"✅ Función de '{funcion.pelicula.nombre}' reactivada correctamente.")
                    
                    # CORRECCIÓN: Recargar los QuerySets después de la reactivación
                    funciones_actuales = Funcion.objects.filter(
                        activa=True,
                        fecha_inicio__gte=hoy_es
                    ).select_related('pelicula').order_by('pelicula__id', 'horario')
                    
                    funciones_pasadas = Funcion.objects.filter(
                        models.Q(activa=False) | models.Q(fecha_inicio__lt=hoy_es)
                    ).select_related('pelicula').order_by('pelicula__id', 'horario')
                    
                except Funcion.DoesNotExist:
                    messages.error(request, "La función que intentas reactivar no existe.")
                except Exception as e:
                    messages.error(request, f"Error al reactivar la función: {str(e)}")
            else:
                messages.error(request, "No se proporcionó ID de función para reactivar.")
            return redirect("administrar_funciones")

        # --- ELIMINAR ---
        elif accion == "eliminar":
            funcion_id = request.POST.get("funcion_id")
            if funcion_id:
                try:
                    funcion = Funcion.objects.get(id=funcion_id)
                    nombre_pelicula = funcion.pelicula.nombre
                    
                    # En lugar de eliminar, marcar como inactiva
                    funcion.activa = False
                    funcion.fecha_eliminacion = hoy_es
                    funcion.save()
                    
                    messages.success(request, f"🗑️ Función de '{nombre_pelicula}' desactivada correctamente.")
                    
                    # CORRECCIÓN: Recargar los QuerySets después de la eliminación
                    funciones_actuales = Funcion.objects.filter(
                        activa=True,
                        fecha_inicio__gte=hoy_es
                    ).select_related('pelicula').order_by('pelicula__id', 'horario')
                    
                    funciones_pasadas = Funcion.objects.filter(
                        models.Q(activa=False) | models.Q(fecha_inicio__lt=hoy_es)
                    ).select_related('pelicula').order_by('pelicula__id', 'horario')
                    
                except Funcion.DoesNotExist:
                    messages.error(request, "La función que intentas eliminar no existe.")
                except Exception as e:
                    messages.error(request, f"Error al eliminar la función: {str(e)}")
            else:
                messages.error(request, "No se proporcionó ID de función para eliminar.")
            return redirect("administrar_funciones")

        # --- EDITAR FUNCIÓN ---
        elif accion == "editar":
            funcion_id = request.POST.get("funcion_id")
            pelicula_id = request.POST.get("pelicula")
            sala_nombre = request.POST.get("sala")
            horario = request.POST.get("horario")
            fecha_inicio_str = request.POST.get("fecha_inicio")
            semanas = request.POST.get("semanas", 1)

            try:
                if not all([funcion_id, pelicula_id, sala_nombre, horario, fecha_inicio_str]):
                    messages.error(request, "❌ Todos los campos son obligatorios.")
                    return redirect("administrar_funciones")

                funcion = Funcion.objects.get(id=funcion_id)
                pelicula = Pelicula.objects.get(id=pelicula_id)
                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()

                # Validar que la fecha no sea pasada
                if fecha_inicio < hoy_es:
                    messages.error(request, "❌ No puedes programar funciones con fecha pasada.")
                    return redirect("administrar_funciones")

                # Validar que la sala exista en las salas disponibles de la película
                salas_pelicula = [sala_tuple[0] for sala_tuple in pelicula.get_salas_con_formato()]
                if sala_nombre not in salas_pelicula:
                    messages.error(request, f"❌ La sala '{sala_nombre}' no está disponible para esta película")
                    return redirect("administrar_funciones")

                # Validar conflicto de horarios (excluyendo la función actual)
                funciones_existentes = Funcion.objects.filter(
                    sala__icontains=sala_nombre,
                    fecha_inicio=fecha_inicio,
                    activa=True
                ).exclude(id=funcion_id)
                
                horarios_existentes = [parse_hora(func.horario) for func in funciones_existentes]
                nuevo_horario = parse_hora(horario)

                if hay_conflicto_distancia(nuevo_horario, horarios_existentes):
                    messages.error(request, f"❌ Conflicto de horarios: la función editada está muy cerca de funciones existentes en la misma sala.")
                    return redirect("administrar_funciones")

                # Actualizar la función
                funcion.pelicula = pelicula
                funcion.sala = sala_nombre  # Guardar como string
                funcion.horario = horario
                funcion.fecha_inicio = fecha_inicio
                funcion.semanas = int(semanas)
                funcion.save()

                messages.success(request, f"✏️ Función editada correctamente: {pelicula.nombre} - {sala_nombre} - {horario}")
                
                # Recargar los QuerySets después de editar
                funciones_actuales = Funcion.objects.filter(
                    activa=True,
                    fecha_inicio__gte=hoy_es
                ).select_related('pelicula').order_by('pelicula__id', 'horario')
                
            except Funcion.DoesNotExist:
                messages.error(request, "❌ La función que intentas editar no existe.")
            except Pelicula.DoesNotExist:
                messages.error(request, "❌ La película seleccionada no existe.")
            except Exception as e:
                messages.error(request, f"❌ Error al editar función: {str(e)}")

    elif request.method == "GET" and "editar" in request.GET:
        funcion_id = request.GET.get("editar")
        if funcion_id:
            try:
                funcion_editar = Funcion.objects.get(id=funcion_id)
            except Funcion.DoesNotExist:
                messages.error(request, "La función que intentas editar no existe.")
        else:
            messages.error(request, "No se proporcionó ID de función para editar.")

    return render(request, "administrar_funciones.html", {
        "peliculas": peliculas,
        "peliculas_con_pares": peliculas_con_pares,
        "funciones_actuales": funciones_actuales,
        "funciones_pasadas": funciones_pasadas,
        "funcion_editar": funcion_editar,
        "HORARIOS_DISPONIBLES": Funcion.HORARIOS_DISPONIBLES,
        "hoy_es": hoy_es,
    })

#########################################################################
### Reportes Administrativos##############################################

from django.db.models import Sum
from django.shortcuts import render
from .models import Venta, Pelicula

from django.db.models import Sum, Q
from django.shortcuts import render
from .models import Venta, Pelicula

@admin_required
def reportes_admin(request):
    peliculas = Pelicula.objects.all()
    pelicula_id = request.GET.get('pelicula')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    reservas = Reserva.objects.all()

    # --- Filtros por fecha y película ---
    if fecha_inicio and fecha_fin:
        reservas = reservas.filter(fecha_reserva__date__range=[fecha_inicio, fecha_fin])

    if pelicula_id:
        reservas = reservas.filter(pelicula_id=pelicula_id)

    # --- Agrupar por película y ordenar por total de boletos (descendente) ---
    reservas_resumen = (
        reservas.values('pelicula__nombre')
        .annotate(
            total_boletos=Sum('cantidad_boletos'),
            total_venta=Sum('precio_total')
        )
        .order_by('-total_boletos')  # 👈 Orden descendente por boletos vendidos
    )

    # --- Calcular boletos por formato (por película) ---
    formatos_disponibles = ['2D', '3D', 'IMAX']
    formatos_info = {}

    for r in reservas_resumen:
        pelicula_nombre = r['pelicula__nombre']
        key = pelicula_nombre
        formatos_info[key] = []

        for formato in formatos_disponibles:
            boletos = reservas.filter(
                pelicula__nombre=pelicula_nombre,
                formato=formato
            ).aggregate(Sum('cantidad_boletos'))['cantidad_boletos__sum'] or 0

            if boletos > 0:
                formatos_info[key].append({
                    'formato': formato,
                    'total_boletos': boletos
                })

    # --- Totales generales ---
    resumen_general = reservas.aggregate(
        total_boletos=Sum('cantidad_boletos'),
        total_ventas=Sum('precio_total')
    )

    # --- Películas más populares ---
    popularidad = (
        reservas.values('pelicula__nombre')
        .annotate(total_boletos=Sum('cantidad_boletos'))
        .order_by('-total_boletos')[:5]
    )

    context = {
        'peliculas': peliculas,
        'ventas_resumen': reservas_resumen,
        'resumen_general': resumen_general,
        'popularidad': popularidad,
        'formatos_info': formatos_info,
    }

    return render(request, 'reportes_admin.html', context)

### Exportar Reportes exell y pdf

def exportar_excel(request):
    # --- Obtener filtros ---
    pelicula_id = request.GET.get('pelicula')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # --- Base de datos ---
    reservas = Reserva.objects.all()
    filtros_activos = False

    if pelicula_id:
        reservas = reservas.filter(pelicula_id=pelicula_id)
        filtros_activos = True

    if fecha_inicio and fecha_fin:
        reservas = reservas.filter(fecha_reserva__date__range=[fecha_inicio, fecha_fin])
        filtros_activos = True

    # --- Agrupar por película ---
    peliculas = reservas.values('pelicula__nombre').annotate(
        total_boletos=Sum('cantidad_boletos'),
        total_venta=Sum('precio_total')
    ).order_by('pelicula__nombre')

    # --- Calcular boletos por formato ---
    datos = []
    for peli in peliculas:
        nombre = peli['pelicula__nombre']
        total_boletos = peli['total_boletos']
        total_venta = peli['total_venta']

        # Obtener datos de formatos
        formatos = reservas.filter(pelicula__nombre=nombre).values('formato').annotate(
            total_boletos=Sum('cantidad_boletos')
        )

        # Combinar datos de formatos en una cadena
        if formatos:
            formatos_texto = ", ".join([f"{f['formato']}: {f['total_boletos']} boletos" for f in formatos])
        else:
            formatos_texto = "Sin formato"

        datos.append({
            "Película": nombre,
            "Boletos por formato": formatos_texto,
            "Total boletos": total_boletos,
            "Total ($)": float(total_venta)
        })

    # --- Calcular totales generales ---
    total_general_boletos = sum(p['Total boletos'] for p in datos)
    total_general_ventas = sum(p['Total ($)'] for p in datos)

    # Agregar fila de totales
    datos.append({
        "Película": "TOTAL GENERAL" if not filtros_activos else "TOTAL FILTRADO",
        "Boletos por formato": "",
        "Total boletos": total_general_boletos,
        "Total ($)": total_general_ventas
    })

    # --- Crear DataFrame ---
    df = pd.DataFrame(datos)

    # --- Crear respuesta con archivo Excel ---
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Nombre dinámico del archivo
    if filtros_activos:
        response["Content-Disposition"] = 'attachment; filename="reporte_filtrado_cinedot.xlsx"'
        hoja_nombre = "Reporte Filtrado"
    else:
        response["Content-Disposition"] = 'attachment; filename="reporte_general_cinedot.xlsx"'
        hoja_nombre = "Reporte General"

    # --- Exportar a Excel ---
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=hoja_nombre)

        hoja = writer.sheets[hoja_nombre]

        # Ajustar ancho de columnas
        for columna in hoja.columns:
            hoja.column_dimensions[columna[0].column_letter].width = 30

        # Fijar encabezados
        hoja.freeze_panes = "A2"

        # Estilo más profesional
        from openpyxl.styles import Font, PatternFill, Alignment

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")

        for cell in hoja[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Centrar contenido
        for fila in hoja.iter_rows(min_row=2, max_row=hoja.max_row):
            for celda in fila:
                celda.alignment = Alignment(horizontal="center", vertical="center")

    return response


### Reportes PDF#########

def exportar_pdf(request):
    # --- Obtener filtros ---
    pelicula_id = request.GET.get('pelicula')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # --- Base de datos ---
    reservas = Reserva.objects.all()
    filtros_activos = False

    if pelicula_id:
        reservas = reservas.filter(pelicula_id=pelicula_id)
        filtros_activos = True

    if fecha_inicio and fecha_fin:
        reservas = reservas.filter(fecha_reserva__date__range=[fecha_inicio, fecha_fin])
        filtros_activos = True

    # --- Crear respuesta PDF ---
    response = HttpResponse(content_type='application/pdf')

    if filtros_activos:
        response['Content-Disposition'] = 'attachment; filename="reporte_filtrado.pdf"'
        titulo = "Reporte Filtrado de Ventas"
    else:
        response['Content-Disposition'] = 'attachment; filename="reporte_general.pdf"'
        titulo = "Reporte General de Ventas (Todas las Películas)"

    # --- Crear PDF en memoria ---
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- Encabezado ---
    p.setFont("Helvetica-Bold", 16)
    p.drawString(130, height - 50, f"🎬 {titulo}")

    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, "Generado automáticamente por el sistema Cinedot")
    p.drawString(50, height - 85, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    y = height - 110

    # --- Mostrar criterios de filtro ---
    if filtros_activos:
        p.setFont("Helvetica-Oblique", 9)
        if pelicula_id:
            peli = Pelicula.objects.get(id=pelicula_id)
            p.drawString(50, y, f"Película: {peli.nombre}")
            y -= 12
        if fecha_inicio and fecha_fin:
            p.drawString(50, y, f"Rango de fechas: {fecha_inicio} a {fecha_fin}")
            y -= 12
        y -= 10

    # --- Encabezado de tabla ---
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Película")
    p.drawString(220, y, "Boletos por formato")
    p.drawString(420, y, "Total boletos")
    p.drawString(510, y, "Total ($)")
    y -= 15
    p.line(50, y, 560, y)
    y -= 20

    # --- Cálculo de datos por película ---
    total_general_boletos = 0
    total_general_ventas = 0

    if reservas.exists():
        # Agrupar por película
        peliculas = reservas.values('pelicula__nombre').annotate(
            total_boletos=Sum('cantidad_boletos'),
            total_venta=Sum('precio_total')
        ).order_by('pelicula__nombre')

        for peli in peliculas:
            nombre = peli['pelicula__nombre']

            # Formatos disponibles por película
            formatos = reservas.filter(pelicula__nombre=nombre).values('formato').annotate(
                total_boletos=Sum('cantidad_boletos')
            )

            # Calcular total
            total_boletos = peli['total_boletos']
            total_venta = peli['total_venta']

            # Mostrar nombre
            p.setFont("Helvetica-Bold", 10)
            p.drawString(50, y, nombre)
            y -= 15

            # Mostrar formatos
            p.setFont("Helvetica", 9)
            if formatos:
                for f in formatos:
                    texto = f"{f['formato']}: {f['total_boletos']} boletos"
                    p.drawString(70, y, texto)
                    y -= 12
            else:
                p.drawString(70, y, "Sin formato")
                y -= 12

            # Mostrar totales por película
            p.setFont("Helvetica-Bold", 10)
            p.drawString(420, y + 5, str(total_boletos))
            p.drawString(510, y + 5, f"${total_venta:.2f}")
            y -= 18

            # Línea divisoria
            p.setFont("Helvetica", 9)
            p.line(50, y, 560, y)
            y -= 10

            total_general_boletos += total_boletos
            total_general_ventas += float(total_venta)

            # Salto de página si se llena
            if y < 100:
                p.showPage()
                y = height - 100

    else:
        p.drawString(50, y, "No hay datos disponibles con los filtros seleccionados.")
        y -= 20

    # --- Totales generales ---
    p.setFont("Helvetica-Bold", 11)
    y -= 10
    p.line(50, y, 560, y)
    y -= 20
    p.drawString(50, y, "Totales generales:")
    p.drawString(420, y, str(total_general_boletos))
    p.drawString(510, y, f"${total_general_ventas:.2f}")

    # --- Guardar PDF ---
    p.showPage()
    p.save()

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from urllib.parse import urlencode
from myapp.email import send_brevo_email  # la función que creamos


class CustomPasswordResetView(PasswordResetView):
    email_template_name = 'registration/password_reset_email.html'  # plantilla del correo
    subject_template_name = 'registration/password_reset_subject.txt'  # asunto

    def send_mail(self, subject, email_template_name, context, from_email, to_email, html_email_template_name=None):
        # Renderizamos el contenido del correo
        html_content = render_to_string(email_template_name, context)
        send_brevo_email(
            to_emails=[to_email],
            subject=subject,
            html_content=html_content
        )



import json



def dashboard_admin(request):
    reservas = Reserva.objects.all()

    top_peliculas = list(
        reservas.values('pelicula__nombre')
        .annotate(
            total_boletos=Sum('cantidad_boletos'),
            total_venta=Sum('precio_total')
        )
        .order_by('-total_boletos')[:10]
    )

    formatos = list(
        reservas.values('formato')
        .annotate(
            total_boletos=Sum('cantidad_boletos'),
            total_venta=Sum('precio_total')
        )
        .order_by('-total_boletos')
    )

    resumen_general = reservas.aggregate(
        total_boletos=Sum('cantidad_boletos'),
        total_ventas=Sum('precio_total')
    )

    context = {
        "resumen_general": resumen_general,
        "top_peliculas": top_peliculas,   # para tablas
        "formatos": formatos,             # para tablas
        "top_peliculas_json": json.dumps(top_peliculas, default=str),
        "formatos_json": json.dumps(formatos, default=str),
    }
    return render(request, "dashboard_admin.html", context)

@login_required
def mis_reservaciones_cancelables(request):
    #Define el limite de tiempo 24 horas
    tiempo_limite = timezone.now() - timedelta(hours=24)
    
    # Filtra las reservas solo de usuarios logueados
    reservas_validas = Reserva.objects.filter(
        usuario=request.user,                 # Solo las del usuario logueado
        fecha_reserva__gte=tiempo_limite,     # Filtrar: Hechas en las últimas 24h
        estado__in=['RESERVADO', 'CONFIRMADO']                      
    ).order_by('-fecha_reserva') 
    
    context = {
        'reservas': reservas_validas,
        'tiempo_limite_cancelacion': 24
    }
    return render(request, 'reservaciones_cancelables.html', context)

@login_required
def cancelar_reserva(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk, usuario=request.user)
    
    
    #tiempo_limite = timezone.now() - timedelta(hours=24)
    TIEMPO_MAXIMO_CANCELACION = timedelta(hours=24)
    tiempo_transcurrido = timezone.now() - reserva.fecha_reserva

    
    if request.method == 'POST':
        #  Verifica si la reserva ya pasó el límite o ya está cancelada
        if tiempo_transcurrido > TIEMPO_MAXIMO_CANCELACION:
            messages.error(request, 'Esta reserva ya no puede ser cancelada.')
            return redirect('mis_reservaciones_cancelables')
            
        #  Cancelar la reserva y invalidar el codigo qr del ticket generado en la reservacion
        reserva.estado = 'CANCELADO'
        reserva.usado = True
        reserva.save()

        try:
            subject = f"Cancelación Exitosa - Reserva {reserva.codigo_reserva}"
            body = (
                f"Hola {reserva.nombre_cliente} {reserva.apellido_cliente},\n\n"
                f"Confirmamos que tu reserva para la película '{reserva.pelicula.nombre}' ha sido **cancelada exitosamente**.\n"
                f"Los asientos {reserva.asientos} de la Sala {reserva.sala} para el horario {reserva.horario} han sido liberados.\n\n"
                f"El proceso de reembolso del monto de ${reserva.precio_total:.2f} se iniciará en las próximas 48 horas (dependiendo de tu banco).\n\n"
                f"¡Esperamos verte pronto en CineDot!"
            )
            
            
            send_brevo_email(
                to_emails=[reserva.email],
                subject=subject,
                html_content=body.replace("\n", "<br>"),
            )
            
        except Exception as e:
            
            print(f" Error al enviar correo de cancelación: {e}") 
            messages.warning(request, f'Reserva cancelada, pero hubo un problema al enviar la notificación por correo.')

        messages.success(request, f'La reserva {reserva.codigo_reserva} ha sido cancelada con éxito.')
        return redirect('mis_reservaciones_cancelables')
        
        return redirect('mis_reservaciones_cancelables')
        
        #messages.success(request, f'La reserva {reserva.codigo_reserva} ha sido cancelada con éxito.')
        #return redirect('mis_reservaciones_cancelables')
        
    # Si es GET, simplemente se redirige o se pide confirmación
   # return redirect('mis_reservaciones_cancelables')