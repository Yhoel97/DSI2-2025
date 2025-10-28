from django.db import models
from django.forms import ValidationError
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Avg

# Create your models here.
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
        ('AN', 'Animacion')
    ]
    
    HORARIOS_DISPONIBLES = [
        '09:30 AM',
        '10:00 AM',
        '12:00 PM',
        '01:30 PM',
        '3:00 PM',
        '5:00 PM',
        '6:00 PM',
        '08:30 PM'
    ]
    
    SALAS_DISPONIBLES = [
        'Sala 1',
        'Sala 2',
        'Sala 3',
        'Sala 4',
        'Sala 5',
        'Sala 6'
    ]

    nombre = models.CharField(max_length=255)
    anio = models.IntegerField()
    fecha_estreno = models.DateField(blank=True, null=True)
    director = models.CharField(max_length=255)
    imagen_url = models.URLField()
    trailer_url = models.URLField()
    generos = models.CharField(max_length=255)
    horarios = models.CharField(max_length=255, blank=True, null=True)
    salas = models.CharField(max_length=255, blank=True, null=True)
    clasificacion = models.CharField(
    max_length=10,
    choices=[
        ('APT', 'Todo Publico'),
        ('13+', 'Mayores de 13 años'),
        ('18+', 'Solo Adultos'),
    ],
    default='APT'  # valor por defecto
    )

    idioma = models.CharField(
    max_length=30,
    choices=[
        ('ESP', 'Español'),
        ('SUB', 'Ingles Sub Titulado'),
        ('ING', 'Inglés'),
    ],
    default='ESP'  # valor por defecto
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_estreno = models.DateField(null=True, blank=True, help_text="Fecha de estreno (opcional)")

    def get_generos_list(self):
        """Devuelve una lista con los nombres completos de los géneros."""
        GENERO_CHOICES_DICT = dict(self.GENERO_CHOICES)
        codigos = [g.strip() for g in self.generos.split(",")] if self.generos else []
        return [GENERO_CHOICES_DICT.get(codigo, codigo) for codigo in codigos] 
    def get_generos_codigos(self):
        """Devuelve lista con los códigos de géneros (ej: ['AC', 'DR'])"""
        return [g.strip() for g in self.generos.split(",")] if self.generos else []


    def get_horarios_list(self):
        return [h.strip() for h in self.horarios.split(",") if h.strip()] if self.horarios else []

    def get_salas_list(self):
        return [s.strip() for s in self.salas.split(",") if s.strip()] if self.salas else []
    
    def horario_sala_pares(self):
        """Devuelve una lista de tuplas (horario, sala) emparejadas correctamente."""
        horarios = self.get_horarios_list()
        salas = self.get_salas_list()
        pares = list(zip(horarios, salas))

    # Si hay más horarios que salas o viceversa, no genera error
        if len(horarios) > len(salas):
           pares += [(h, '') for h in horarios[len(salas):]]
        elif len(salas) > len(horarios):
           pares += [('', s) for s in salas[len(horarios):]]

        return pares


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


from django.db import models
from datetime import date

class Funcion(models.Model):
    pelicula = models.ForeignKey('Pelicula', on_delete=models.CASCADE)
    fecha = models.DateField()
    horario = models.CharField(max_length=50)
    sala = models.CharField(max_length=50)
    formato = models.CharField(
        max_length=10,
        choices=[('2D', '2D'), ('3D', '3D'), ('IMAX', 'IMAX')],
        default='2D'
    )

    def __str__(self):
        return f"{self.pelicula.nombre} - {self.fecha} ({self.horario} - {self.sala})"

    class Meta:
        ordering = ['fecha', 'horario']



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
