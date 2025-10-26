from io import BytesIO
from zipfile import ZipFile
import json
import random
import string
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
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from urllib.parse import urlencode
from .email import send_brevo_email
import base64
import logging


# Diccionario de géneros con nombres completos
GENERO_CHOICES_DICT = {
    "AC": "Acción",
    "DR": "Drama",
    "CO": "Comedia",
    "TE": "Terror",
    "CF": "Ciencia Ficción",
    "RO": "Romance",
    "DO": "Documental",
    "AN": "Animacion"
}

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

def convertir_generos(codigos_generos):
    """Convierte códigos de género a nombres completos"""
    if not codigos_generos:
        return []
    return [GENERO_CHOICES_DICT.get(codigo.strip(), "Desconocido") 
            for codigo in codigos_generos.split(",")]

def index(request):
    hoy = date.today()

    # ✅ Traer las funciones del día actual
    funciones = (
        Funcion.objects.filter(fecha=hoy)
        .select_related('pelicula')
        .order_by('pelicula__nombre', 'horario')
    )

    # ✅ Agrupar funciones por película
    peliculas_cartelera = []
    for pelicula, grupo_funciones in groupby(funciones, key=lambda f: f.pelicula):
        pelicula.funciones = list(grupo_funciones)
        peliculas_cartelera.append(pelicula)

    # ✅ Películas base de datos y próximas (sin tocar)
    peliculas = Pelicula.objects.filter(
        models.Q(fecha_estreno__lte=hoy) | models.Q(fecha_estreno__isnull=True)
    ).order_by('-id')

    peliculas_proximas = Pelicula.objects.filter(
        fecha_estreno__gt=hoy
    ).order_by('fecha_estreno')

    for pelicula in peliculas:
        pelicula.get_generos_list = convertir_generos(pelicula.generos)
        horarios = pelicula.get_horarios_list()
        salas = pelicula.get_salas_list()
        pelicula.horario_sala_pares = list(zip(horarios, salas))
        pelicula.estrellas = (
            pelicula.get_rating_estrellas()
            if hasattr(pelicula, 'get_rating_estrellas')
            else {'llenas': 0, 'media': False}
        )

    for pelicula in peliculas_proximas:
        pelicula.get_generos_list = convertir_generos(pelicula.generos)

    es_admin = request.user.is_authenticated and request.user.is_staff

    return render(request, 'index.html', {
        'peliculas': peliculas,
        'peliculas_proximas': peliculas_proximas,
        'peliculas_cartelera': peliculas_cartelera,  # 👈 agrupadas
        'es_admin': es_admin,
    })



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

@csrf_exempt
def asientos(request, pelicula_id=None):
    pelicula = get_object_or_404(Pelicula, pk=pelicula_id) if pelicula_id else None
    
    if not pelicula:
        messages.error(request, "No se ha seleccionado ninguna película")
        return redirect('index')
    
    if request.method == 'POST':
        nombre_cliente = request.POST.get('nombre_cliente', '').strip()
        apellido_cliente = request.POST.get('apellido_cliente', '').strip()
        email = request.POST.get('email', '').strip()
        formato = request.POST.get('formato', '').strip()
        combo = request.POST.get('combo', '').strip()  # Ej: "09:30 AM - Sala 1"
        asientos_seleccionados = request.POST.get('asientos', '').strip()

        salas_list = pelicula.get_salas_list()
        horarios_list = pelicula.get_horarios_list()
        combinaciones = [f"{h} - {s}" for h, s in zip(horarios_list, salas_list)]

        errores = []
        if not nombre_cliente: errores.append('El nombre es obligatorio')
        if not apellido_cliente: errores.append('El apellido es obligatorio')
        if not email or '@' not in email: errores.append('Ingrese un email válido')
        if not formato or formato not in dict(Reserva.FORMATO_CHOICES).keys(): errores.append('Seleccione un formato válido')
        if not combo or combo not in combinaciones: errores.append('Seleccione una combinación válida')
        if not asientos_seleccionados: errores.append('Seleccione al menos un asiento')

        if not errores:
            try:
                horario, sala = combo.split(" - ", 1)
                precio_por_boleto = {'2D': 3.50, '3D': 4.50, 'IMAX': 6.00}.get(formato, 0)
                cantidad_boletos = len([a for a in asientos_seleccionados.split(',') if a])
                
                #Descuento
                precio_subtotal = float(precio_por_boleto * cantidad_boletos)
                descuento_porcentaje = float(request.session.get('descuento_porcentaje', 0))
                codigo_aplicado = request.session.get('codigo_aplicado')
                
                monto_descuento = precio_subtotal * (descuento_porcentaje / 100)
                precio_total = precio_subtotal - monto_descuento
                
                reserva = Reserva(
                    pelicula=pelicula,
                    nombre_cliente=nombre_cliente,
                    apellido_cliente=apellido_cliente,
                    email=email,
                    formato=formato,
                    sala=sala.strip(),
                    horario=horario.strip(),
                    asientos=asientos_seleccionados,
                    cantidad_boletos=cantidad_boletos,
                    precio_total=precio_total,
                    estado='RESERVADO'
                )
                reserva.codigo_reserva = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

                # Limpia las variables de session del cupon para otras compras
                if 'descuento_porcentaje' in request.session:
                    del request.session['descuento_porcentaje']
                if 'codigo_aplicado' in request.session:
                    del request.session['codigo_aplicado']
                
                reserva.save()

                reserva.save()

                # ✅ Registrar la venta automáticamente
                try:
                   Venta.objects.create(
                       pelicula=reserva.pelicula,
                       sala=reserva.sala,
                       fecha=date.today(),
                       cantidad_boletos=reserva.cantidad_boletos,
                       total_venta=reserva.precio_total
                    )
                except Exception as e:
                    print(f"⚠️ Error al registrar la venta: {e}")

                pdf_buffer = generar_pdf_reserva(reserva)
                response = HttpResponse(pdf_buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="ticket_{reserva.codigo_reserva}.pdf"'

                request.session['reserva_message'] = f'¡Reserva exitosa! Código: {reserva.codigo_reserva}'
                request.session['limpiar_form'] = True
                
                return response

            except Exception as e:
                messages.error(request, f'Error al crear la reserva: {str(e)}')
        else:
            for error in errores:
                messages.error(request, error)

    # Mensaje post-reserva
    if 'reserva_message' in request.session:
        messages.success(request, request.session['reserva_message'])
        del request.session['reserva_message']

    salas_list = pelicula.get_salas_list()
    horarios_list = pelicula.get_horarios_list()
    combinaciones = [f"{h} - {s}" for h, s in zip(horarios_list, salas_list)]

    combo_actual = request.POST.get('combo') or request.GET.get('combo') or (combinaciones[0] if combinaciones else '')

    asientos_ocupados = []
    if combo_actual:
        try:
            horario_sel, sala_sel = combo_actual.split(" - ", 1)
            reservas_existentes = Reserva.objects.filter(
                pelicula=pelicula,
                sala=sala_sel.strip(),
                horario=horario_sel.strip(),
                estado__in=['RESERVADO', 'CONFIRMADO']
            )
            for r in reservas_existentes:
                asientos_ocupados.extend(r.get_asientos_list())
        except ValueError:
            pass
 
    if request.method == 'GET':
        request.session.pop('descuento_porcentaje', None)
        request.session.pop('codigo_aplicado', None)
        request.session.pop('mensaje_cupon', None)

    descuento_porcentaje = request.session.get('descuento_porcentaje', 0)
    mensaje_cupon = request.session.pop('mensaje_cupon', '') 

    context = {
        'pelicula': pelicula,
        'formatos': Reserva.FORMATO_CHOICES,
        'asientos_ocupados': asientos_ocupados,
        'combinaciones': combinaciones,
        'combo_actual': combo_actual,
        'descuento_porcentaje': float(descuento_porcentaje), 
        'mensaje_cupon': mensaje_cupon,
        'limpiar_form': request.session.pop('limpiar_form', False),
    }
    return render(request, "asientos.html", context)


##########################################################################################
##########################################################################################



logger = logging.getLogger(__name__)

def enviar_ticket_por_correo(reserva, pdf_buffer, email_cliente):
    """
    Envía el ticket PDF por correo al cliente usando tu función Brevo
    """
    try:
        subject = f'Tu ticket para {reserva.pelicula.nombre} - CineDot'
        
        # Mensaje simple en HTML
        html_content = '''
        <html>
            <body>
                <p>Aquí está tu ticket.</p>
                <p>Gracias por preferir a CineDot.</p>
            </body>
        </html>
        '''

        # Convertir PDF a base64 para adjuntar
        pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode()
        
        # Preparar el adjunto
        attachments = [{
            'name': f'ticket_{reserva.codigo_reserva}.pdf',
            'content': pdf_base64
        }]
        
        # Llamar a tu función de Brevo con el adjunto
        send_brevo_email(
            to_emails=[email_cliente],
            subject=subject,
            html_content=html_content,
            attachments=attachments
        )
        
        logger.info(f"Ticket enviado exitosamente a {email_cliente}")
        return True

    except Exception as e:
        logger.error(f"Error al enviar ticket por correo: {str(e)}")
        return False

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
###############################################################################################

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
            horarios = request.POST.getlist('horarios')
            salas = request.POST.getlist('salas')
            fecha_estreno = request.POST.get('fecha_estreno', '').strip()
            clasificacion = request.POST.get('clasificacion', 'APT')
            idioma = request.POST.get('idioma', 'Español')

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
                    horarios=",".join(horarios),
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
            pelicula.horarios = ",".join(request.POST.getlist('horarios'))
            pelicula.salas = ",".join(request.POST.getlist('salas'))
            pelicula.fecha_estreno = request.POST.get('fecha_estreno') or None
            pelicula.clasificacion = request.POST.get('clasificacion', 'APT')
            pelicula.idioma = request.POST.get('idioma', 'Español')
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
    horarios_disponibles = Pelicula.HORARIOS_DISPONIBLES
    salas_disponibles = Pelicula.SALAS_DISPONIBLES

    pelicula_editar = None
    if 'editar' in request.GET:
        nombre = request.GET.get('editar')
        pelicula_editar = Pelicula.objects.filter(nombre=nombre).first()
                # ✅ Asegurar que los géneros carguen correctamente al editar
        if pelicula_editar:
            pelicula_editar.get_generos_list = pelicula_editar.get_generos_list()
            pelicula_editar.get_horarios_list = pelicula_editar.get_horarios_list()
            pelicula_editar.get_salas_list = pelicula_editar.get_salas_list()


    # 🔹 Convertir películas de cartelera con sus pares horarios/salas
    peliculas_con_pares = []
    for p in peliculas_en_cartelera:
        pares = list(zip(p.get_horarios_list(), p.get_salas_list()))
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
        'HORARIOS_DISPONIBLES': horarios_disponibles,
        'SALAS_DISPONIBLES': salas_disponibles,
        'pelicula_editar': pelicula_editar,
        'busqueda': busqueda,
    }

    return render(request, 'peliculas.html', context)




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

######

def filtrar_peliculas(request):
    genero = request.GET.get('genero', '').strip()
    clasificacion = request.GET.get('clasificacion', '').strip()
    idioma = request.GET.get('idioma', '').strip()
    horario = request.GET.get('horario', '').strip()

    hoy = date.today()

    # 🔹 Películas con funciones activas hoy
    peliculas = Pelicula.objects.filter(funcion__fecha=hoy).distinct()

    # 🔹 Aplicar filtros si el usuario los usa
    if genero:
        peliculas = peliculas.filter(generos__icontains=genero)
    if clasificacion:
        peliculas = peliculas.filter(clasificacion__icontains=clasificacion)
    if idioma:
        peliculas = peliculas.filter(idioma__icontains=idioma)
    if horario:
        peliculas = peliculas.filter(funcion__horario__icontains=horario)

    peliculas = peliculas.order_by('-fecha_estreno', '-id')

    # 🔹 Construir los datos combinando Pelicula + Funcion
    peliculas_data = []
    for p in peliculas:
        funciones_hoy = Funcion.objects.filter(pelicula=p, fecha=hoy)
        horarios = [f.horario for f in funciones_hoy]
        salas = [f.sala for f in funciones_hoy]
        pares = list(zip(horarios, salas))

        peliculas_data.append({
            'id': p.id,
            'nombre': p.nombre,
            'imagen_url': p.imagen_url,
            'anio': p.anio,
            'director': p.director or "No especificado",
            'generos': ", ".join(p.get_generos_list()) if hasattr(p, 'get_generos_list') else p.generos,
            'clasificacion': p.clasificacion or "No definida",
            'idioma': p.idioma or "No especificado",
            'fecha_estreno': p.fecha_estreno,
            'pares': pares,  # 🔹 horarios y salas reales de hoy
        })

    context = {
        'peliculas': peliculas_data,
        'genero': genero,
        'clasificacion': clasificacion,
        'idioma': idioma,
        'horario': horario,
        'GENERO_CHOICES': Pelicula.GENERO_CHOICES,
        'CLASIFICACION_CHOICES': Pelicula._meta.get_field('clasificacion').choices,
        'IDIOMA_CHOICES': Pelicula._meta.get_field('idioma').choices,
        'HORARIOS_DISPONIBLES': Pelicula.HORARIOS_DISPONIBLES,
    }

    return render(request, 'filtrar.html', context)
#######

def horarios_por_pelicula(request):
    """
    Muestra solo películas con funciones activas HOY,
    agrupando todos sus horarios y salas.
    """
    hoy = date.today()

    # Filtros opcionales del formulario
    genero = request.GET.get('genero', '').strip()
    clasificacion = request.GET.get('clasificacion', '').strip()
    idioma = request.GET.get('idioma', '').strip()

    # 🎬 Solo películas que tienen funciones hoy (agrupadas por película)
    peliculas = Pelicula.objects.filter(
        funcion__fecha=hoy
    ).prefetch_related(
        Prefetch('funcion_set', queryset=Funcion.objects.filter(fecha=hoy))
    ).distinct()

    # 🔍 Aplicar filtros si el usuario selecciona alguno
    if genero:
        peliculas = peliculas.filter(generos__icontains=genero)
    if clasificacion:
        peliculas = peliculas.filter(clasificacion__icontains=clasificacion)
    if idioma:
        peliculas = peliculas.filter(idioma__icontains=idioma)

    peliculas = peliculas.order_by('-fecha_estreno', '-id')

    # 🔹 Construir lista de películas con horarios y salas del día
    peliculas_data = []
    for p in peliculas:
        funciones_hoy = p.funcion_set.all()  # gracias al prefetch_related, no hace más queries
        pares = [(f.horario, f.sala) for f in funciones_hoy]

        peliculas_data.append({
            'id': p.id,
            'nombre': p.nombre,
            'imagen_url': p.imagen_url,
            'generos': ", ".join(p.get_generos_list()),
            'clasificacion': p.clasificacion,
            'idioma': p.idioma,
            'anio': p.anio,
            'fecha_estreno': p.fecha_estreno,
            'pares': pares,
        })

    context = {
        'peliculas': peliculas_data,
        'fecha': hoy,
        'genero': genero,
        'clasificacion': clasificacion,
        'idioma': idioma,
        'GENERO_CHOICES': Pelicula.GENERO_CHOICES,
        'CLASIFICACION_CHOICES': Pelicula._meta.get_field('clasificacion').choices,
        'IDIOMA_CHOICES': Pelicula._meta.get_field('idioma').choices,
    }

    return render(request, 'horarios.html', context)

@admin_required
def administrar_funciones(request):
    hoy = date.today()
    peliculas = Pelicula.objects.all().order_by("nombre")
    funciones = Funcion.objects.select_related('pelicula').order_by('fecha', 'horario')

    # Listas de opciones desde el modelo
    HORARIOS_DISPONIBLES = Pelicula.HORARIOS_DISPONIBLES
    SALAS_DISPONIBLES = Pelicula.SALAS_DISPONIBLES

    funcion_editar = None

    # --- CREAR, EDITAR o ELIMINAR FUNCIÓN ---
    if request.method == "POST":
        accion = request.POST.get("accion")

        # --- ELIMINAR ---
        if accion == "eliminar":
            funcion_id = request.POST.get("funcion_id")
            if not funcion_id:
                messages.error(request, "No se especificó la función a eliminar.")
                return redirect("administrar_funciones")

            funcion = get_object_or_404(Funcion, id=funcion_id)
            funcion.delete()
            messages.success(request, "🗑️ Función eliminada correctamente.")
            return redirect("administrar_funciones")

        # --- CREAR o EDITAR ---
        pelicula_id = request.POST.get("pelicula")
        fecha = request.POST.get("fecha")

        # 🔹 En el nuevo template, los horarios, salas y formatos vienen como listas
        horarios = request.POST.getlist("horario[]")
        salas = request.POST.getlist("sala[]")
        formatos = request.POST.getlist("formato[]")

        if not (pelicula_id and fecha and horarios and salas):
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect("administrar_funciones")

        pelicula = get_object_or_404(Pelicula, id=pelicula_id)

        # --- Validaciones generales ---
        if pelicula.fecha_estreno and pelicula.fecha_estreno > hoy:
            messages.warning(
                request,
                f"⚠️ '{pelicula.nombre}' es un próximo estreno (se estrena el {pelicula.fecha_estreno.strftime('%d/%m/%Y')}). "
                "No se puede crear una función antes de esa fecha."
            )
            return redirect("administrar_funciones")

        # --- EDITAR (solo una función, como antes) ---
        if accion == "editar":
            funcion_id_editar = request.POST.get("funcion_id")
            funcion = get_object_or_404(Funcion, id=funcion_id_editar)
            horario = horarios[0] if horarios else None
            sala = salas[0] if salas else None
            formato = formatos[0] if formatos else "2D"

            # Reutilizamos las mismas validaciones que tenías
            funciones_en_sala_qs = Funcion.objects.filter(fecha=fecha, sala=sala).exclude(id=funcion_id_editar)
            if funciones_en_sala_qs.count() >= 3:
                messages.warning(request, f"⚠️ Solo se permiten 3 funciones por día en {sala}.")
                return redirect("administrar_funciones")

            duplicada_qs = Funcion.objects.filter(
                pelicula=pelicula, fecha=fecha, horario=horario, sala=sala
            ).exclude(id=funcion_id_editar)
            if duplicada_qs.exists():
                messages.error(request, "❌ Ya existe una función para esta película en ese horario y sala.")
                return redirect("administrar_funciones")

            conflicto_qs = Funcion.objects.filter(
                fecha=fecha, horario=horario, sala=sala
            ).exclude(id=funcion_id_editar).exclude(pelicula=pelicula)
            if conflicto_qs.exists():
                messages.error(request, f"❌ En {sala} ya hay otra película programada a las {horario}.")
                return redirect("administrar_funciones")

            # Guardamos cambios
            funcion.pelicula = pelicula
            funcion.fecha = fecha
            funcion.horario = horario
            funcion.sala = sala
            funcion.formato = formato
            funcion.save()
            messages.success(request, "✏️ Función actualizada correctamente.")
            return redirect("administrar_funciones")

        # --- CREAR (puede crear múltiples funciones a la vez) ---
        elif accion == "crear":
            creadas = 0
            for i in range(len(horarios)):
                horario = horarios[i]
                sala = salas[i] if i < len(salas) else ""
                formato = formatos[i] if i < len(formatos) else "2D"

                # Validaciones individuales (reusando las tuyas)
                if Funcion.objects.filter(fecha=fecha, sala=sala).count() >= 3:
                    messages.warning(request, f"⚠️ Solo se permiten 3 funciones por día en {sala}.")
                    continue

                if Funcion.objects.filter(
                    pelicula=pelicula, fecha=fecha, horario=horario, sala=sala
                ).exists():
                    messages.warning(request, f"⏰ '{pelicula.nombre}' ya tiene una función en {sala} a las {horario}.")
                    continue

                if Funcion.objects.filter(
                    fecha=fecha, horario=horario, sala=sala
                ).exclude(pelicula=pelicula).exists():
                    messages.warning(request, f"⚠️ En {sala} ya hay otra película a las {horario}.")
                    continue

                Funcion.objects.create(
                    pelicula=pelicula,
                    fecha=fecha,
                    horario=horario,
                    sala=sala,
                    formato=formato
                )
                creadas += 1

            if creadas:
                messages.success(request, f"✅ {creadas} función(es) agregada(s) correctamente.")
            else:
                messages.warning(request, "⚠️ No se agregaron funciones por conflictos o duplicados.")
            return redirect("administrar_funciones")

        else:
            messages.error(request, "Acción no reconocida.")
            return redirect("administrar_funciones")

    # --- MODO EDICIÓN ---
    elif request.method == "GET" and "editar" in request.GET:
        funcion_id = request.GET.get("editar")
        funcion_editar = get_object_or_404(Funcion, id=funcion_id)

    return render(request, "administrar_funciones.html", {
        "peliculas": peliculas,
        "funciones": funciones,
        "funcion_editar": funcion_editar,
        "HORARIOS_DISPONIBLES": HORARIOS_DISPONIBLES,
        "SALAS_DISPONIBLES": SALAS_DISPONIBLES,
    })



### Reportes Administrativos

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

 # la función que creamos


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
