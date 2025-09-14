from django .urls import path
from . import views 
from django.urls import path



urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.my_login, name='login'),
    path('registro/', views.registro_usuario, name='registro'),
    path('peliculas/', views.peliculas, name='peliculas'),

    path('asientos/<int:pelicula_id>/', views.asientos, name='asientos'),
    path('ticket/<str:codigo_reserva>/', views.descargar_ticket, name='descargar_ticket'),
    path('validaQR/<str:codigo_reserva>/', views.validaQR, name='validaQR'),
    
    # URLs para valoraciones - PBI-24
    path('pelicula/<int:pelicula_id>/', views.pelicula_detalle, name='pelicula_detalle'),
    path('pelicula/<int:pelicula_id>/valorar/', views.crear_valoracion, name='crear_valoracion'),
    path('pelicula/<int:pelicula_id>/eliminar-valoracion/', views.eliminar_valoracion, name='eliminar_valoracion'),
    
]