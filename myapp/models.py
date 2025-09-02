from django.db import models
from django.forms import ValidationError
from django.urls import reverse

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
    director = models.CharField(max_length=255)
    imagen_url = models.URLField()
    trailer_url = models.URLField()
    generos = models.CharField(max_length=255)
    horarios = models.CharField(max_length=255, blank=True, null=True)
    salas = models.CharField(max_length=255, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def get_generos_list(self):
        return self.generos.split(",") if self.generos else []

    def get_horarios_list(self):
        return [h.strip() for h in self.horarios.split(",")] if self.horarios else []
        
    def get_salas_list(self):
        return [s.strip() for s in self.salas.split(",")] if self.salas else []

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'peliculas'




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

    class Meta:
        db_table = 'reservas'
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'