from django.contrib import admin
from django.urls import path, include
from core import views  

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # PÁGINAS PÚBLICAS
    path('', views.home, name='home'),
    path('historia/', views.historia, name='historia'),
    path('servicios/', views.servicios, name='servicios'),
    path('contacto/', views.contacto, name='contacto'),

    # API WHISPER (La nueva conexión con Unity)
    path('api/transcribir-audio/', views.transcribir_audio, name='transcribir_audio'),
    path('api/guardar-progreso/', views.guardar_progreso, name='guardar_progreso'),

    #API MocaTest
    path('api/guardar-moca/', views.guardar_moca, name='guardar_moca'),

    # RUTAS DE AUTENTICACIÓN
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/registro/', views.registro, name='registro'),

    # PANEL PACIENTE
    path('dashboard/', views.dashboard, name='dashboard'),
    path('mi-progreso/', views.resumen_paciente, name='resumen_paciente'),
    path('terapia/', views.juegos, name='juegos'),
    path('terapia/test-memoria/', views.jugar_moca_5, name='jugar_moca_5'),
    path('terapia/test-memoria-definitivo/', views.jugar_moca_5_definitivo, name='jugar_moca_5_definitivo'),
    path('terapia/elsa/', views.jugar_elsa, name='jugar_elsa'),
    path('terapia/calculadora/', views.jugar_calculadora, name='jugar_calculadora'),
    path('terapia/encuentra-letra/', views.jugar_encuentra_letra, name='jugar_encuentra_letra'),
    path('api/guardar-progreso/', views.guardar_progreso, name='guardar_progreso'),
    path('terapia/prueba-voz/', views.jugar_prueba_voz, name='jugar_prueba_voz'),
    path('terapia/identificacion-elsa/', views.jugar_identificacion_elsa_unity, name='jugar_identificacion_elsa_unity'),
    path('buzon/', views.buzon_paciente, name='buzon_paciente'),
     # URL de la API que recibe el audio y usa Whisper (MUY IMPORTANTE)
    path('api/transcribir-audio/', views.transcribir_audio, name='transcribir_audio'),


    
    # PANEL MÉDICO 
    path('paciente/<int:pk>/', views.detalle_paciente, name='detalle_paciente'),
    path('medico/paciente/<int:pk>/analisis/', views.analisis_paciente, name='analisis_paciente'),
    path('evaluacion/', views.sala_evaluacion, name='sala_evaluacion'),
    path('forzar-evaluacion/<int:pk>/', views.forzar_evaluacion, name='forzar_evaluacion'),
    path('medico/dashboard/', views.dashboard_medico, name='dashboard_medico'),
    path('paciente/<int:pk>/moca/', views.historial_moca, name='historial_moca'),
    path('auditoria-moca/<int:pk_evaluacion>/', views.auditoria_moca, name='auditoria_moca'),
    path('medico/paciente/<int:pk>/buzon/', views.buzon_paciente_medico, name='buzon_paciente_medico'),
]