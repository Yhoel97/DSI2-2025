from django .urls import path
from . import views 
from django.urls import path



urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.my_login, name = 'login'),
    path('peliculas/', views.peliculas, name= 'peliculas'),

   path('asientos/<int:pelicula_id>/', views.asientos, name='asientos'),
    path('ticket/<str:codigo_reserva>/', views.descargar_ticket, name='descargar_ticket'),

    
]