from io import BytesIO
import json
from multiprocessing import context
import random
import string
from tkinter import CENTER, Canvas
from turtle import color
from django.shortcuts import render, redirect
from django.urls import reverse
from DSI2025 import settings
from .forms import *
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Pelicula, Reserva
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

def convertir_generos(codigos_generos):
    """Convierte códigos de género a nombres completos"""
    if not codigos_generos:
        return []
    return [GENERO_CHOICES_DICT.get(codigo.strip(), "Desconocido") 
            for codigo in codigos_generos.split(",")]

def index(request):
    peliculas = Pelicula.objects.all().order_by('-fecha_creacion')[:10]  # Últimas 10 películas
    
    # Convertir los códigos de género a nombres completos
    for pelicula in peliculas:
        pelicula.get_generos_list = convertir_generos(pelicula.generos)

    return render(request, 'index.html', {'peliculas': peliculas})

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
                
            next_url = request.POST.get('next', '/peliculas/')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'registration/login.html')

#######################################################################

@csrf_exempt
def asientos(request, pelicula_id=None):
    # Obtener la película seleccionada
    pelicula = get_object_or_404(Pelicula, pk=pelicula_id) if pelicula_id else None
    
    if not pelicula:
        messages.error(request, "No se ha seleccionado ninguna película")
        return redirect('index')
    
    if request.method == 'POST':
        nombre_cliente = request.POST.get('nombre_cliente', '').strip()
        apellido_cliente = request.POST.get('apellido_cliente', '').strip()
        email = request.POST.get('email', '').strip()
        formato = request.POST.get('formato', '').strip()
        horario = request.POST.get('horario', '').strip()
        sala = request.POST.get('sala', '').strip()
        asientos_seleccionados = request.POST.get('asientos', '').strip()
        
        errores = []
        
        if not nombre_cliente: errores.append('El nombre es obligatorio')
        if not apellido_cliente: errores.append('El apellido es obligatorio')
        if not email or '@' not in email: errores.append('Ingrese un email válido')
        if not formato or formato not in dict(Reserva.FORMATO_CHOICES).keys(): errores.append('Seleccione un formato válido')
        if not horario or horario not in pelicula.get_horarios_list(): errores.append('Seleccione un horario válido')
        if not sala or sala not in pelicula.get_salas_list(): errores.append('Seleccione una sala válida')
        if not asientos_seleccionados: errores.append('Seleccione al menos un asiento')
        
        if not errores:
            try:
                precio_por_boleto = {
                    '2D': 3.50,
                    '3D': 4.50,
                    'IMAX': 6.00
                }.get(formato, 0)
                
                cantidad_boletos = len(asientos_seleccionados.split(','))
                precio_total = precio_por_boleto * cantidad_boletos
                
                reserva = Reserva(
                    pelicula=pelicula,
                    nombre_cliente=nombre_cliente,
                    apellido_cliente=apellido_cliente,
                    email=email,
                    formato=formato,
                    sala=sala,
                    horario=horario,
                    asientos=asientos_seleccionados,
                    cantidad_boletos=cantidad_boletos,
                    precio_total=precio_total,
                    estado='RESERVADO'
                )
                
                reserva.codigo_reserva = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                reserva.save()
                
                # Generar PDF
                pdf_buffer = generar_pdf_reserva(reserva)
                
                # Crear respuesta
                response = HttpResponse(pdf_buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="ticket_{reserva.codigo_reserva}.pdf"'
                
                # Guardar mensaje en sesión para mostrarlo después
                request.session['reserva_message'] = f'¡Reserva exitosa! Código: {reserva.codigo_reserva}'
                
                return response
                
            except Exception as e:
                messages.error(request, f'Error al crear la reserva: {str(e)}')
        else:
            for error in errores:
                messages.error(request, error)
    
    # Mostrar mensaje de reserva exitosa si existe
    if 'reserva_message' in request.session:
        messages.success(request, request.session['reserva_message'])
        del request.session['reserva_message']
    
    context = {
        'pelicula': pelicula,
        'formatos': Reserva.FORMATO_CHOICES,
    }
    return render(request, "asientos.html", context)

#################################################################


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
    logo_path = os.path.abspath(os.path.join(settings.BASE_DIR, 'myapp', 'static', 'imagenes', 'cine.jpg'))
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2*inch, height=1*inch)
        elements.append(logo)
    
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

    # Generar la URL usando reverse
    asientos_url = reverse('asientos', kwargs={'pelicula_id': reserva.pelicula.id})
    
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket_{reserva.codigo_reserva}.pdf"'
    
    # Agregar script JavaScript para redirección
    response.write(
        '<script>'
        'window.addEventListener("load", function() {'
        '  setTimeout(function() {'
        f'    window.location.href = "{asientos_url}";'
        '  }, 1000);'
        '});'
        '</script>'
    )
    
    
    return render(request, "asientos.html", context)
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

@csrf_exempt
def peliculas(request):
    # Obtener todas las películas para mostrar en la tabla
    peliculas_list = Pelicula.objects.all().order_by('-fecha_creacion')
    
    # Procesar búsqueda si existe
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        peliculas_list = peliculas_list.filter(
            Q(nombre__icontains=busqueda) | 
            Q(director__icontains=busqueda)
        )
    
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
                        salas=",".join(salas)
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
            director = request.POST.get('director', '').strip()
            imagen_url = request.POST.get('imagen_url', '').strip()
            trailer_url = request.POST.get('trailer_url', '').strip()
            generos = request.POST.getlist('generos')
            horarios = request.POST.getlist('horarios')
            salas = request.POST.getlist('salas')
            
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
    
    context = {
        'peliculas': peliculas_list,
        'GENERO_CHOICES_DICT': generos_choices,
        'HORARIOS_DISPONIBLES': horarios_disponibles,
        'SALAS_DISPONIBLES': salas_disponibles,
        'pelicula_editar': pelicula_editar,
        'busqueda': busqueda,
    }
    
    return render(request, 'peliculas.html', context)