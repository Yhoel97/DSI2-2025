from django.urls import path, include
from . import views
from django.urls import path, include
from myapp.views import CustomPasswordResetView


urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.my_login, name='login'),
    path('logout/', views.my_logout, name='my_logout'),
    path('registro/', views.registro_usuario, name='registro'),
    path('panelAdmin/', views.panel_admin, name='panelAdmin'),
    path('peliculas/', views.peliculas, name='peliculas'),
    path('peliculas/filtrar/', views.filtrar_peliculas, name='filtrar_peliculas'),
    path('horarios/', views.horarios_por_pelicula, name='horarios_por_pelicula'),
    path('dashboard/', views.dashboard_admin, name='dashboard_admin'),


    path('asientos/<int:pelicula_id>/', views.asientos, name='asientos'),
    path('ticket/<str:codigo_reserva>/', views.descargar_ticket, name='descargar_ticket'),
    path('validaQR/<str:codigo_reserva>/', views.validaQR, name='validaQR'),
    path('administrar_salas/', views.administrar_salas, name='administrar_salas'),
    
    # URLs para valoraciones - PBI-24
    path('pelicula/<int:pelicula_id>/', views.pelicula_detalle, name='pelicula_detalle'),
    path('pelicula/<int:pelicula_id>/valorar/', views.crear_valoracion, name='crear_valoracion'),
    path('pelicula/<int:pelicula_id>/eliminar-valoracion/', views.eliminar_valoracion, name='eliminar_valoracion'),
    #URLS para modulo cupones
      path('cupones/registrar/', views.registrar_cupon, name='registrar_cupon'),
    path('cupones/eliminar/<int:pk>/', views.eliminar_cupon, name='eliminar_cupon'), 
    path('cupones/modificar/<int:pk>/', views.modificar_cupon, name='modificar_cupon'),
    path('aplicar_descuento/', views.aplicar_descuento_ajax, name='aplicar_descuento_ajax'),

    #PBI-018 Administrar funciones
    path('administrar_funciones/', views.administrar_funciones, name='administrar_funciones'),

   # path('', include('django.contrib.auth.urls')),



    # PBI 28 Reportes Administrativos
    path('reportes/', views.reportes_admin, name='reportes_admin'),
    path('exportar_excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar_pdf/', views.exportar_pdf, name='exportar_pdf'),

  # Rutas password reset
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
   # path('accounts/', include('django.contrib.auth.urls')),  # esto incluye las demás vistas (login, logout, etc.)

    path('mis_reservaciones/', views.mis_reservaciones_cancelables, name='mis_reservaciones_cancelables'),
    path('reserva/cancelar/<int:pk>/', views.cancelar_reserva, name='cancelar_reserva'),
    
    # URLs para gestión de métodos de pago - PBI-27
    path('mis-metodos-pago/', views.mis_metodos_pago, name='mis_metodos_pago'),
    path('metodos-pago/agregar/', views.agregar_metodo_pago, name='agregar_metodo_pago'),
    path('metodos-pago/editar/<int:metodo_id>/', views.editar_metodo_pago, name='editar_metodo_pago'),
    path('metodos-pago/eliminar/<int:metodo_id>/', views.eliminar_metodo_pago, name='eliminar_metodo_pago'),
    path('metodos-pago/predeterminado/<int:metodo_id>/', views.marcar_predeterminado, name='marcar_predeterminado'),

    # PBI-29: Gestión de Usuarios
    path('administrar_usuarios/', views.administrar_usuarios, name='administrar_usuarios'),

]

