from io import BytesIO
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
from .models import Pelicula, Reserva, Valoracion
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
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
from django.shortcuts import render
from django.urls import reverse


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

   peliculas = Pelicula.objects.filter(
        models.Q(fecha_estreno__lte=hoy) | models.Q(fecha_estreno__isnull=True)
    ).order_by('-id')

   peliculas_proximas = Pelicula.objects.filter(
        fecha_estreno__gt=hoy
    ).order_by('fecha_estreno')

    # Procesar listas de géneros y horarios
   for pelicula in peliculas:
        pelicula.get_generos_list = convertir_generos(pelicula.generos)
        horarios = pelicula.get_horarios_list()
        salas = pelicula.get_salas_list()
        pelicula.horario_sala_pares = list(zip(horarios, salas))

   for pelicula in peliculas_proximas:
        pelicula.get_generos_list = convertir_generos(pelicula.generos)

   return render(request, 'index.html', {
        'peliculas': peliculas,
        'peliculas_proximas': peliculas_proximas
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

        # Listas base
        salas_list = pelicula.get_salas_list()
        horarios_list = pelicula.get_horarios_list()
        # Emparejar uno a uno por índice
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
                precio_total = precio_por_boleto * cantidad_boletos

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
                reserva.save()

                pdf_buffer = generar_pdf_reserva(reserva)
                response = HttpResponse(pdf_buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="ticket_{reserva.codigo_reserva}.pdf"'

                # Señal para limpiar storage en el siguiente load
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

    # Listas base
    salas_list = pelicula.get_salas_list()
    horarios_list = pelicula.get_horarios_list()
    # Emparejar uno a uno por índice (tres opciones si hay 3 y 3)
    combinaciones = [f"{h} - {s}" for h, s in zip(horarios_list, salas_list)]

    # Combo actual por GET/POST o primer emparejamiento
    combo_actual = request.POST.get('combo') or request.GET.get('combo') or (combinaciones[0] if combinaciones else '')

    # Asientos ocupados según combo actual
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
            pass  # combo malformado en edge cases

    context = {
        'pelicula': pelicula,
        'formatos': Reserva.FORMATO_CHOICES,
        'asientos_ocupados': asientos_ocupados,
        'combinaciones': combinaciones,
        'combo_actual': combo_actual,
        'limpiar_form': request.session.pop('limpiar_form', False),
    }
    return render(request, "asientos.html", context)

#################################################################
#################################################################
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
@admin_required
@csrf_exempt
def peliculas(request):
    # Procesar búsqueda primero
    busqueda = request.GET.get('busqueda', '').strip()
    
    # Primero se filtra, luego se limita
    peliculas_list = Pelicula.objects.all().order_by('-id')
    if busqueda:
        peliculas_list = peliculas_list.filter(
            Q(nombre__icontains=busqueda) | Q(director__icontains=busqueda)
        )
    
    # Finalmente tomamos solo las últimas 10 (después del filtro)
    peliculas_list = peliculas_list[:10]

    
    # Procesar formulario para crear/editar/eliminar
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'crear':
            # Validar y crear nueva película
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
            # Validaciones
            errores = []
            
            if not nombre:
                errores.append('El nombre es obligatorio')
            if Pelicula.objects.filter(nombre=nombre).exists():
                errores.append('Ya existe una película con ese nombre')
            if not anio.isdigit() or int(anio) < 1900 or int(anio) > 2099:
                errores.append('El año debe ser entre 1900 y 2099')
            if not director:
                errores.append('El director es obligatorio')
            if not imagen_url:
                errores.append('La URL de la imagen es obligatoria')
            if not trailer_url:
                errores.append('La URL del trailer es obligatoria')
            if len(generos) == 0:
                errores.append('Debe seleccionar al menos un género')
            if len(generos) > 3:
                errores.append('No puede seleccionar más de 3 géneros')
            if len(horarios) == 0:
                errores.append('Debe seleccionar al menos un horario')
            if len(salas) == 0:
                errores.append('Debe seleccionar al menos una sala')
            
            if not errores:
                try:
                    pelicula = Pelicula(
                        nombre=nombre,
                        anio=int(anio),
                        director=director,
                        imagen_url=imagen_url,
                        trailer_url=trailer_url,
                        generos=",".join(generos),
                        horarios=",".join(horarios),
    
                        fecha_estreno=fecha_estreno if fecha_estreno else None,
                        clasificacion=clasificacion,
                        idioma=idioma
                    )

                    pelicula.save()
                    messages.success(request, f'Película "{nombre}" creada exitosamente!')
                    return redirect('peliculas')
                except Exception as e:
                    messages.error(request, f'Error al crear la película: {str(e)}')
            else:
                for error in errores:
                    messages.error(request, error)
                
        elif accion == 'editar':
            # Obtener datos del formulario
            nombre_original = request.POST.get('nombre_original', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            anio = request.POST.get('anio', '').strip()
            fecha_estreno = request.POST.get('fecha_estreno', '').strip()
            director = request.POST.get('director', '').strip()
            imagen_url = request.POST.get('imagen_url', '').strip()
            trailer_url = request.POST.get('trailer_url', '').strip()
            generos = request.POST.getlist('generos')
            horarios = request.POST.getlist('horarios')
            salas = request.POST.getlist('salas')
            clasificacion = request.POST.get('clasificacion', 'APT')
            idioma = request.POST.get('idioma', 'Español')       
            # Validaciones
            errores = []
            
            if not nombre_original:
                errores.append('No se especificó la película a editar')
            if not nombre:
                errores.append('El nombre es obligatorio')
            if nombre != nombre_original and Pelicula.objects.filter(nombre=nombre).exists():
                errores.append('Ya existe otra película con ese nombre')
            if not anio.isdigit() or int(anio) < 1900 or int(anio) > 2099:
                errores.append('El año debe ser entre 1900 y 2099')
            if not director:
                errores.append('El director es obligatorio')
            if not imagen_url:
                errores.append('La URL de la imagen es obligatoria')
            if not trailer_url:
                errores.append('La URL del trailer es obligatoria')
            if len(generos) == 0:
                errores.append('Debe seleccionar al menos un género')
            if len(generos) > 3:
                errores.append('No puede seleccionar más de 3 géneros')
            if len(horarios) == 0:
                errores.append('Debe seleccionar al menos un horario')
            if len(salas) == 0:
                errores.append('Debe seleccionar al menos una sala')
            
            if not errores:
                try:
                    pelicula = Pelicula.objects.get(nombre=nombre_original)
                    pelicula.nombre = nombre
                    pelicula.anio = int(anio)
                    pelicula.director = director
                    pelicula.imagen_url = imagen_url
                    pelicula.trailer_url = trailer_url
                    pelicula.generos = ",".join(generos)
                    pelicula.horarios = ",".join(horarios)
                    pelicula.salas = ",".join(salas)
                    pelicula.fecha_estreno = fecha_estreno if fecha_estreno else None
                    pelicula.clasificacion = clasificacion
                    pelicula.idioma = idioma
                    if fecha_estreno:
                        from datetime import datetime
                        try:
                            pelicula.fecha_estreno = datetime.strptime(fecha_estreno, '%Y-%m-%d').date()
                        except ValueError:
                            messages.warning(request, '⚠️ Formato de fecha inválido. Usa AAAA-MM-DD.')
                    else:
                        pelicula.fecha_estreno = None
                    pelicula.save()
                    messages.success(request, f'Película "{nombre}" actualizada exitosamente!')
                    return redirect('peliculas')
                except Pelicula.DoesNotExist:
                    messages.error(request, 'La película que intentas editar no existe')
                except Exception as e:
                    messages.error(request, f'Error al actualizar la película: {str(e)}')
            else:
                for error in errores:
                    messages.error(request, error)
                
        elif accion == 'eliminar':
            nombre = request.POST.get('nombre', '').strip()
            if nombre:
                try:
                    pelicula = Pelicula.objects.get(nombre=nombre)
                    pelicula.delete()
                    messages.success(request, f'Película "{nombre}" eliminada exitosamente!')
                    return redirect('peliculas')
                except Pelicula.DoesNotExist:
                    messages.error(request, 'La película que intentas eliminar no existe')
                except Exception as e:
                    messages.error(request, f'Error al eliminar la película: {str(e)}')
            else:
                messages.error(request, 'No se especificó la película a eliminar')
    
    # Preparar datos para el template
    generos_choices = dict(Pelicula.GENERO_CHOICES)
    horarios_disponibles = Pelicula.HORARIOS_DISPONIBLES
    salas_disponibles = Pelicula.SALAS_DISPONIBLES
    
    # Si estamos editando, cargar los datos de la película
    pelicula_editar = None
    if 'editar' in request.GET:
        nombre = request.GET.get('editar')
        try:
            pelicula_editar = Pelicula.objects.get(nombre=nombre)
        except Pelicula.DoesNotExist:
            messages.error(request, f'No se encontró la película "{nombre}" para editar')
    
    # ✅ Corrección: append correctamente indentado
    peliculas_con_pares = []
    for p in peliculas_list:
        pares = p.horario_sala_pares()
        generos_nombres = [
            generos_choices.get(g, g)
            for g in p.get_generos_list()
        ]
        peliculas_con_pares.append({
            'obj': p,
            'pares': pares,
            'generos_nombres': ", ".join(generos_nombres),
            'clasificacion': p.clasificacion,
            'idioma': p.idioma
        })

    context = {
        'peliculas': peliculas_con_pares,
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
    genero = request.GET.get('genero')
    clasificacion = request.GET.get('clasificacion')
    idioma = request.GET.get('idioma')
    horario = request.GET.get('horario')

    peliculas = Pelicula.objects.all()

    # 🔹 Filtro por género (convertir nombre a código si es necesario)
    if genero and genero.strip():
        genero = genero.strip()
        # Buscar tanto por código como por nombre
        peliculas = peliculas.filter(
            models.Q(generos__icontains=genero) |
            models.Q(generos__icontains=dict(Pelicula.GENERO_CHOICES).get(genero, genero))
        )

    # 🔹 Filtro por clasificación
    if clasificacion and clasificacion.strip():
        peliculas = peliculas.filter(clasificacion=clasificacion.strip())

    # 🔹 Filtro por idioma
    if idioma and idioma.strip():
        peliculas = peliculas.filter(idioma=idioma.strip())

    # 🔹 Filtro por horario
    if horario and horario.strip():
        peliculas = peliculas.filter(horarios__icontains=horario.strip())

    peliculas = peliculas.distinct().order_by('-fecha_creacion')

    context = {
        'peliculas': peliculas,
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
    """PBI-14: Visualizar horarios agrupados por película"""
    peliculas = Pelicula.objects.all().order_by('-fecha_creacion')

    peliculas_data = []
    for p in peliculas:
        horarios = p.get_horarios_list()
        salas = p.get_salas_list()
        pares = list(zip(horarios, salas))  # Emparejar horarios y salas
        
        peliculas_data.append({
            'id': p.id,
            'nombre': p.nombre,
            'imagen_url': p.imagen_url,
            'generos': ", ".join(p.get_generos_list()),
            'clasificacion': p.clasificacion,
            'idioma': p.idioma,
            'anio': p.anio,
            'fecha_estreno': p.fecha_estreno,
            'pares': pares
        })

    context = {
        'peliculas': peliculas_data
    }
    return render(request, 'horarios.html', context)


