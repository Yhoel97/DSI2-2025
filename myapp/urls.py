from django .urls import path
from . import views 
from django.urls import path



urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.my_login, name = 'login'),
    path('peliculas/', views.peliculas, name= 'peliculas'),

    path('asientos/<int:pelicula_id>/', views.asientos, name='asientos'),
    path('ticket/<str:codigo_reserva>/', views.descargar_ticket, name='descargar_ticket'),
    path('validaQR/<str:codigo_reserva>/', views.validaQR, name='validaQR'),
<<<<<<< HEAD
    path('salas/', views.administrar_salas, name='administrar_salas'),
=======
    
>>>>>>> b08f8cd52b5331abfcaf46aa0151c789ebb2afa2
]