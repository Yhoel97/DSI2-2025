from datetime import timedelta
from django.db import models
from django.forms import ValidationError
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Avg
from django.db import models


class Pelicula(models.Model):
    GENERO_CHOICES = [
        ('AC', 'Acción'),
        ('DR', 'Drama'),
        ('CO', 'Comedia'),
        ('TE', 'Terror'),
        ('CF', 'Ciencia Ficción'),
        ('RO', 'Romance'),
        ('DO', 'Documental'),
        ('AN', 'Animación'),
        ('FA', 'Fantasía'), 
    ]

    #  cada sala tiene formato asociado
    SALAS_DISPONIBLES = {
        'Sala 1': '2D',
        'Sala 2': '2D',
        'Sala 3': '2D',
        'Sala 4': '2D',
        'Sala 5': '3D',
        'Sala 6': '3D',
        'Sala 7': 'IMAX',
        'Sala 8': 'IMAX',
    }

    nombre = models.CharField(max_length=255)
    anio = models.IntegerField()
    fecha_estreno = models.DateField(blank=True, null=True)
    director = models.CharField(max_length=255)
    imagen_url = models.URLField()
    trailer_url = models.URLField()
    generos = models.CharField(max_length=255)
    salas = models.CharField(max_length=255, blank=True, null=True)

    clasificacion = models.CharField(
        max_length=10,
        choices=[
            ('APT', 'Todo Público'),
            ('13+', 'Mayores de 13 años'),
            ('18+', 'Solo Adultos'),
        ],
        default='APT'
    )

    idioma = models.CharField(
        max_length=30,
        choices=[
            ('ESP', 'Español'),
            ('SUB', 'Inglés Subtitulado'),
            ('ING', 'Inglés'),
        ],
        default='ESP'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_estreno = models.DateField(null=True, blank=True, help_text="Fecha de estreno (opcional)")

    # ---------------- MÉTODOS ---------------- #

    def get_generos_list(self):
        """Devuelve una lista con los nombres completos de los géneros."""
        GENERO_CHOICES_DICT = dict(self.GENERO_CHOICES)
        codigos = [g.strip() for g in self.generos.split(",")] if self.generos else []
        return [GENERO_CHOICES_DICT.get(codigo, codigo) for codigo in codigos]

    def get_generos_codigos(self):
        """Devuelve lista con los códigos de géneros (ej: ['AC', 'DR'])"""
        return [g.strip() for g in self.generos.split(",")] if self.generos else []

    def get_salas_list(self):
        return [s.strip() for s in self.salas.split(",") if s.strip()] if self.salas else []

    def get_salas_con_formato(self):
        """Devuelve lista de tuplas (sala, formato)."""
        return [(s, self.SALAS_DISPONIBLES.get(s, '')) for s in self.get_salas_list()]

    def get_rating_promedio(self):
        """Obtiene el rating promedio de la película"""
        promedio = self.valoraciones.aggregate(promedio=Avg('rating'))['promedio']
        return round(promedio, 1) if promedio else 0

    def get_total_valoraciones(self):
        """Obtiene el total de valoraciones de la película"""
        return self.valoraciones.count()

    def get_rating_estrellas(self):
        """Obtiene la representación en estrellas del rating promedio"""
        promedio = self.get_rating_promedio()
        estrellas_llenas = int(promedio)
        tiene_media = (promedio - estrellas_llenas) >= 0.5
        return {
            'llenas': estrellas_llenas,
            'media': tiene_media,
            'vacias': 5 - estrellas_llenas - (1 if tiene_media else 0),
            'promedio': promedio
        }

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'peliculas'

####################################################################

from django.db import models
from datetime import timedelta, datetime
import pytz

class Funcion(models.Model):
    # Horarios disponibles: valor en 24h, etiqueta en AM/PM
    HORARIOS_DISPONIBLES = [
        ("10:00", "10:00 AM"), ("10:30", "10:30 AM"),
        ("11:00", "11:00 AM"), ("11:30", "11:30 AM"),
        ("12:00", "12:00 PM"), ("12:30", "12:30 PM"),
        ("13:00", "1:00 PM"), ("13:30", "1:30 PM"),
        ("14:00", "2:00 PM"), ("14:30", "2:30 PM"),
        ("15:00", "3:00 PM"), ("15:30", "3:30 PM"),
        ("16:00", "4:00 PM"), ("16:30", "4:30 PM"),
        ("17:00", "5:00 PM"), ("17:30", "5:30 PM"),
        ("18:00", "6:00 PM"), ("18:30", "6:30 PM"),
        ("19:00", "7:00 PM"), ("19:30", "7:30 PM"),
    ]

    pelicula = models.ForeignKey(
        'Pelicula',
        on_delete=models.CASCADE,
        related_name="funciones"
    )
    fecha_inicio = models.DateField(
        null=True, blank=True,
        help_text="Fecha de inicio de la programación"
    )
    semanas = models.PositiveIntegerField(
        default=1,
        help_text="Duración en semanas (1–8)"
    )
    horario = models.CharField(
        max_length=20,
        choices=HORARIOS_DISPONIBLES
    )
    sala = models.CharField(max_length=50)
    
    # ✅ NUEVOS CAMPOS
    activa = models.BooleanField(default=True, help_text="Si la función sigue activa")
    fecha_eliminacion = models.DateField(
        null=True, 
        blank=True, 
        help_text="Fecha en que se eliminó la función"
    )
    
    def get_duracion_real(self):
        """Calcula la duración real en días que estuvo activa la función"""
        if not self.fecha_inicio:
            return 0
        
        # Si fue eliminada manualmente
        if self.fecha_eliminacion:
            delta = self.fecha_eliminacion - self.fecha_inicio
            return max(delta.days + 1, 1)  # Mínimo 1 día
        
        # Si está inactiva pero no tiene fecha_eliminacion
        if not self.activa:
            from datetime import date
            hoy = date.today()
            # Solo calcular si la fecha de inicio es en el pasado
            if self.fecha_inicio <= hoy:
                delta = hoy - self.fecha_inicio
                return max(delta.days + 1, 1)
            else:
                return 0
    
        # Si está activa, devolver las semanas programadas
        return self.semanas * 7
    

    def get_formato_sala(self):
            """Obtiene SOLO el formato de la sala (2D, 3D, IMAX)"""
            try:
                return self.pelicula.SALAS_DISPONIBLES.get(self.sala, "")
            except:
                return ""
    
    def get_info_completa(self):
        """Retorna el string formateado completo: horario - sala - formato"""
        horario_display = dict(self.HORARIOS_DISPONIBLES).get(self.horario, self.horario)
        formato = self.get_formato_sala()
        return f"{horario_display} - {self.sala} - {formato}"

    def fecha_fin(self):
        """Calcula la fecha de finalización real"""
        # Si fue eliminada antes, usar esa fecha
        if self.fecha_eliminacion:
            return self.fecha_eliminacion
        
        # Si no, calcular la fecha programada
        if self.fecha_inicio and self.semanas:
            return self.fecha_inicio + timedelta(weeks=self.semanas) - timedelta(days=1)
        return None
    
    def esta_vigente(self):
        """Verifica si la función está vigente"""
        from datetime import date
        hoy = date.today()
        
        # Si fue marcada como inactiva, no está vigente
        if not self.activa:
            return False
        
        # Si la fecha de inicio es futura, aún no está vigente
        if self.fecha_inicio and self.fecha_inicio > hoy:
            return False
        
        # Si ya pasó su fecha de fin, no está vigente
        fecha_finalizacion = self.fecha_fin()
        if fecha_finalizacion and fecha_finalizacion < hoy:
            return False
        
        return True

    def __str__(self):
        return f"{self.pelicula.nombre} - {self.sala} ({self.get_horario_display()})"

    class Meta:
        ordering = ['fecha_inicio', 'horario']

#################################################################
class Reserva(models.Model):
    FORMATO_CHOICES = [
        ('2D', '2D - $3.50'),
        ('3D', '3D - $4.50'),
        ('IMAX', 'IMAX - $6.00'),
    ]
    
    ESTADO_CHOICES = [
        ('RESERVADO', 'Reservado'),
        ('CONFIRMADO', 'Confirmado'),
        ('CANCELADO', 'Cancelado'),
    ]
    #Se agrego para que funcione correctamente el modulo de cancelacion de reservas
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE)
    nombre_cliente = models.CharField(max_length=100)
    apellido_cliente = models.CharField(max_length=100)
    email = models.EmailField()
    formato = models.CharField(max_length=4, choices=FORMATO_CHOICES)
    sala = models.CharField(max_length=50)
    horario = models.CharField(max_length=50)
    asientos = models.CharField(max_length=255)
    cantidad_boletos = models.PositiveIntegerField(default=1)
    precio_total = models.DecimalField(max_digits=6, decimal_places=2)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='RESERVADO')
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    codigo_reserva = models.CharField(max_length=10, unique=True)
    usado = models.BooleanField(default=False)
    fecha_funcion = models.DateField(null=True, blank=True, help_text="Fecha de la función reservada")
    
    # Campos de pago - PBI-30
    pago_completado = models.BooleanField(default=False, help_text="Indica si el pago fue completado")
    fecha_pago = models.DateTimeField(null=True, blank=True, help_text="Fecha y hora en que se completó el pago")

    def __str__(self):
        return f"Reserva #{self.codigo_reserva} - {self.pelicula.nombre}"

    def clean(self):
        super().clean()
        if self.cantidad_boletos != len(self.asientos.split(',')):
            raise ValidationError("La cantidad de boletos no coincide con los asientos seleccionados")
        if self.cantidad_boletos > 10:
            raise ValidationError("No se pueden reservar más de 10 boletos por transacción")

    def save(self, *args, **kwargs):
        if not self.codigo_reserva:
            self.codigo_reserva = self.generar_codigo()
        super().save(*args, **kwargs)
    
    def generar_codigo(self):
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def get_asientos_list(self):
        return self.asientos.split(',')
    
    class Meta:
        db_table = 'reservas'
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'


class Valoracion(models.Model):
    RATING_CHOICES = [
        (1, '1 estrella'),
        (2, '2 estrellas'),
        (3, '3 estrellas'),
        (4, '4 estrellas'),
        (5, '5 estrellas'),
    ]
    
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE, related_name='valoraciones')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    resena = models.TextField(max_length=500, blank=True, null=True, 
                             help_text="Escribe tu reseña (opcional, máximo 500 caracteres)")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def get_rating_estrellas(self):
        """Obtiene la representación en estrellas del rating"""
        return {
            'llenas': self.rating,
            'vacias': 5 - self.rating,
            'rating': self.rating
        }

    def __str__(self):
        return f"{self.usuario.username} - {self.pelicula.nombre} ({self.rating}/5)"

    class Meta:
        unique_together = ('pelicula', 'usuario')
        verbose_name = 'Valoración'
        verbose_name_plural = 'Valoraciones'
        ordering = ['-fecha_creacion']

#Tabla CodigoDescuento
class CodigoDescuento(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    estado = models.BooleanField(default=True)  
    

    def _str_(self):
        return f"{self.codigo} - {self.porcentaje}%"
    
### Clase para reportes administrativos PBI 28
    
class Venta(models.Model):
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE)
    sala = models.CharField(max_length=50)
    fecha = models.DateField()
    cantidad_boletos = models.PositiveIntegerField()
    total_venta = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.pelicula.nombre} - {self.fecha}"


#################################################################
# MODELOS PARA SISTEMA DE PAGO - PBI-27 y PBI-30
#################################################################

class Pago(models.Model):
    """Modelo para registrar pagos de reservas"""
    
    ESTADO_PAGO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
        ('REEMBOLSADO', 'Reembolsado'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('TARJETA', 'Tarjeta de Crédito/Débito'),
        ('CUENTA_DIGITAL', 'Cuenta Digital'),
    ]
    
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=8, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    estado_pago = models.CharField(max_length=15, choices=ESTADO_PAGO_CHOICES, default='PENDIENTE')
    fecha_pago = models.DateTimeField(auto_now_add=True)
    numero_transaccion = models.CharField(max_length=50, unique=True, help_text="Número único de transacción")
    detalles_pago = models.JSONField(null=True, blank=True, help_text="Información adicional del pago")
    # metodo_pago_guardado se agregará en migración posterior (Fase 2)
    # metodo_pago_guardado = models.ForeignKey('MetodoPago', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Pago {self.numero_transaccion} - {self.get_estado_pago_display()}"
    
    class Meta:
        db_table = 'pagos'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_pago']
