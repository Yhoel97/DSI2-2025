from django.contrib import admin
from .models import Pelicula, Funcion, Reserva, Valoracion, CodigoDescuento, Venta, Pago

# Register your models here.

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'numero_transaccion', 'monto', 'metodo_pago', 'estado_pago', 'fecha_pago', 'get_reserva_codigo')
    list_filter = ('estado_pago', 'metodo_pago', 'fecha_pago')
    search_fields = ('numero_transaccion', 'reserva__codigo_reserva', 'reserva__email')
    readonly_fields = ('fecha_pago', 'numero_transaccion', 'detalles_pago')
    date_hierarchy = 'fecha_pago'
    
    fieldsets = (
        ('Información de la Transacción', {
            'fields': ('numero_transaccion', 'fecha_pago', 'monto', 'estado_pago')
        }),
        ('Método de Pago', {
            'fields': ('metodo_pago',)
        }),
        ('Reserva Asociada', {
            'fields': ('reserva',)
        }),
        ('Detalles Adicionales', {
            'fields': ('detalles_pago',),
            'classes': ('collapse',)
        }),
    )
    
    def get_reserva_codigo(self, obj):
        return obj.reserva.codigo_reserva if obj.reserva else 'Sin reserva'
    get_reserva_codigo.short_description = 'Código de Reserva'
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar registros de pago por auditoría
        return False
    
    def has_add_permission(self, request):
        # Los pagos solo se crean desde la aplicación
        return False

