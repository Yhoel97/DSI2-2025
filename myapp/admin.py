from django.contrib import admin
from .models import Pelicula, Funcion, Reserva, Valoracion, CodigoDescuento, Venta, Pago, MetodoPago

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


@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'alias', 'tipo', 'get_info_resumida', 'es_predeterminado', 'activo', 'fecha_creacion')
    list_filter = ('tipo', 'es_predeterminado', 'activo', 'tipo_tarjeta', 'tipo_cuenta')
    search_fields = ('usuario__username', 'usuario__email', 'alias', 'ultimos_4_digitos', 'email_cuenta')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'datos_encriptados')
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Información Básica', {
            'fields': ('tipo', 'alias', 'es_predeterminado', 'activo')
        }),
        ('Datos de Tarjeta', {
            'fields': ('tipo_tarjeta', 'ultimos_4_digitos', 'mes_expiracion', 'anio_expiracion', 'nombre_titular'),
            'classes': ('collapse',)
        }),
        ('Datos de Cuenta Digital', {
            'fields': ('tipo_cuenta', 'email_cuenta'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'datos_encriptados'),
            'classes': ('collapse',)
        }),
    )
    
    def get_info_resumida(self, obj):
        if obj.tipo == 'TARJETA':
            return f"{obj.get_tipo_tarjeta_display()} ****{obj.ultimos_4_digitos}"
        else:
            return f"{obj.get_tipo_cuenta_display()} - {obj.email_cuenta}"
    get_info_resumida.short_description = 'Información'
    
    def has_delete_permission(self, request, obj=None):
        # Permitir eliminar desde admin (usar con precaución)
        return request.user.is_superuser


