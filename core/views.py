from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from .forms import RegistroUsuarioForm
from .models import PerfilPaciente, SesionDeJuego, NotaEspecialista
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import whisper
import os
import tempfile
from django.contrib.auth.models import User

# --- CONFIGURACIÓN WHISPER ---
MODELO_WHISPER = None

# =========================================================
# VISTAS PÚBLICAS
# =========================================================
def home(request):
    return render(request, "core/pages/home.html")

def historia(request):
    return render(request, "core/patients/historia.html")

def servicios(request):
    return render(request, "core/pages/servicios.html")

def contacto(request):
    return render(request, "core/pages/contacto.html")

# --- VISTA DE REGISTRO ---
def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Intento robusto de detectar perfil médico
            es_medico = False
            try:
                if hasattr(user, 'perfil'): # Si related_name='perfil'
                    es_medico = user.perfil.es_medico
                elif hasattr(user, 'perfilpaciente'): # Si es el default
                    es_medico = user.perfilpaciente.es_medico
            except:
                pass

            if es_medico:
                return redirect('dashboard_medico') 
            else:
                return redirect('dashboard')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'registration/registro.html', {'form': form})

# =========================================================
# ZONA PRIVADA (PACIENTE)
# =========================================================

@login_required
def dashboard(request):
    perfil, created = PerfilPaciente.objects.get_or_create(usuario=request.user)
    if perfil.es_medico:
        return redirect('dashboard_medico')
    if not perfil.test_completado:
        return redirect('sala_evaluacion')
    return redirect('juegos') 

@login_required
def resumen_paciente(request):
    perfil, created = PerfilPaciente.objects.get_or_create(usuario=request.user)
    context = {'perfil': perfil}
    return render(request, 'core/dashboard/dashboard.html', context)

# =========================================================
# ZONA PRIVADA (MÉDICO)
# =========================================================

@login_required
def dashboard_medico(request):
    perfil, created = PerfilPaciente.objects.get_or_create(usuario=request.user)
    if not perfil.es_medico:
        return redirect('dashboard')

    mis_pacientes = PerfilPaciente.objects.filter(medico_asignado=request.user)
    total_pacientes = mis_pacientes.count()
    
    context = {
        'pacientes': mis_pacientes,
        'total_pacientes': total_pacientes
    }
    return render(request, 'core/dashboard/dashboard_medico.html', context)

@login_required
def detalle_paciente(request, pk):
    perfil_paciente = get_object_or_404(PerfilPaciente, pk=pk)
    
    if request.method == 'POST':
        # 1. Si el médico actualiza los niveles
        if 'actualizar_niveles' in request.POST:
            try:
                perfil_paciente.nivel_cognitivo = int(request.POST.get('nivel_cognitivo', 1))
                perfil_paciente.nivel_lenguaje = int(request.POST.get('nivel_lenguaje', 1))
                perfil_paciente.nivel_motor = int(request.POST.get('nivel_motor', 1))
                perfil_paciente.nivel_asignado = perfil_paciente.nivel_cognitivo
                perfil_paciente.save()
                messages.success(request, "Niveles actualizados correctamente.")
            except ValueError:
                messages.error(request, "Error al actualizar los niveles.")
            return redirect('detalle_paciente', pk=pk)
            
        # 2. Si el médico guarda una nota nueva
        elif 'guardar_nota' in request.POST:
            texto_nota = request.POST.get('texto_nota', '').strip()
            if texto_nota:
                NotaEspecialista.objects.create(
                    paciente=perfil_paciente,
                    medico=request.user,
                    texto=texto_nota
                )
                messages.success(request, "Nota clínica guardada en el historial.")
            return redirect('detalle_paciente', pk=pk)

    # Obtenemos todas las notas del paciente
    notas = perfil_paciente.notas.all()
    
    # Hemos eliminado la lógica de la gráfica general de puntos y fechas
    
    context = {
        'paciente': perfil_paciente,
        'notas': notas,
    }
    return render(request, 'core/patients/detalle_paciente.html', context)

@login_required
def forzar_evaluacion(request, pk):
    perfil = get_object_or_404(PerfilPaciente, pk=pk)
    perfil.test_completado = False
    perfil.nivel_asignado = 0
    perfil.save()
    messages.success(request, f"Se ha solicitado re-evaluación para {perfil.usuario.username}.")
    return redirect('dashboard_medico')

# =========================================================
# SISTEMA DE JUEGOS (RUTAS ACTUALIZADAS A TUS CARPETAS)
# =========================================================

@login_required
def juegos(request):
    return render(request, 'core/juegos.html')

@login_required
def jugar(request):
    return render(request, 'core/jugar.html')

@login_required
def sala_evaluacion(request):
    perfil, created = PerfilPaciente.objects.get_or_create(usuario=request.user)
    if request.method == 'POST':
        nivel_elegido = int(request.POST.get('resultado_simulado'))
        
        # --- ASIGNACIÓN INICIAL MÚLTIPLE ---
        # Al hacer el test, asignamos el mismo nivel a las 3 áreas para empezar
        perfil.nivel_asignado = nivel_elegido
        perfil.nivel_cognitivo = nivel_elegido
        perfil.nivel_lenguaje = nivel_elegido
        perfil.nivel_motor = nivel_elegido
        
        perfil.puntuacion_cognitiva = nivel_elegido * 6 
        perfil.test_completado = True
        perfil.fecha_ultima_evaluacion = timezone.now()
        perfil.save()
        return redirect('dashboard')
    return render(request, 'core/patients/evaluacion.html')

# --- JUEGOS DE LENGUAJE / MOCA ---
@login_required
def jugar_moca_5(request):
    # Ruta basada en tu captura: games/moca/
    return render(request, 'core/games/moca/juego_moca5.html')

@login_required
def jugar_moca_5_definitivo(request):
    # Ruta basada en tu captura: games/moca/
    return render(request, 'core/games/moca/juego_moca5_definitivo.html')

@login_required
def jugar_elsa(request):
    # Ruta basada en tu captura: games/moca/
    return render(request, 'core/games/moca/juego_elsa.html')

@login_required
def jugar_calculadora(request):
    # Ruta basada en tu captura: games/moca/
    return render(request, 'core/games/moca/juego_calculadora.html')

# --- JUEGOS MOTORES ---
@login_required
def jugar_prueba_camara(request):
    # Ruta basada en tu captura: games/motor/
    return render(request, 'core/games/motor/juego_prueba_camara.html')

# --- JUEGOS COGNITIVOS (El nuevo) ---
@login_required
def jugar_encuentra_letra(request):
    try:
        perfil = request.user.perfil 
    except:
        perfil = None

    # --- CAMBIO CLAVE: Usamos el nivel específico COGNITIVO ---
    nivel_actual = perfil.nivel_cognitivo if perfil else 1
    
    context = {
        'nivel_inicial': nivel_actual
    }
    # Ruta basada en tu captura: games/cognitivo/
    return render(request, 'core/games/cognitivo/atencion/juego_encuentra_letra.html', context)

@login_required
def jugar_prueba_voz(request):
    # Una vista simple para probar el micrófono y Whisper
    return render(request, 'core/games/Lenguaje/juego_prueba_voz.html')


# =========================================================
# FUNCIONES API (GUARDADO Y WHISPER)
# =========================================================
def evaluar_ajuste_dinamico(perfil, nombre_juego):
    """
    Sistema Universal de Ajuste Dinámico de Dificultad (DDA).
    Analiza las últimas 2 sesiones del dominio correspondiente al juego actual.
    """
    # 1. DICCIONARIO DE DOMINIOS (Aquí clasificamos los juegos)
    JUEGOS_COGNITIVOS = ["Encuentra la Letra", "Calculadora", "Juego 1: Memoria", "Memoria MoCA"]
    JUEGOS_LENGUAJE = ["Juego de Elsa", "Laboratorio Voz"]
    JUEGOS_MOTORES = ["Prueba de Cámara"]
    
    dominio = None
    nivel_actual = 1
    lista_juegos_dominio = []
    
    # Detectamos a qué dominio pertenece el juego jugado
    if nombre_juego in JUEGOS_COGNITIVOS:
        dominio = "Cognitivo"
        nivel_actual = perfil.nivel_cognitivo
        lista_juegos_dominio = JUEGOS_COGNITIVOS
    elif nombre_juego in JUEGOS_LENGUAJE:
        dominio = "Lenguaje"
        nivel_actual = perfil.nivel_lenguaje
        lista_juegos_dominio = JUEGOS_LENGUAJE
    elif nombre_juego in JUEGOS_MOTORES:
        dominio = "Motor"
        nivel_actual = perfil.nivel_motor
        lista_juegos_dominio = JUEGOS_MOTORES
        
    # Si el juego no está registrado en ninguna lista, salimos por seguridad
    if not dominio:
        return
        
    # 2. Obtenemos las últimas 2 sesiones SOLO de ese dominio
    ultimas_sesiones = SesionDeJuego.objects.filter(
        paciente=perfil, 
        juego__in=lista_juegos_dominio
    ).order_by('-fecha')[:2]
        
    if len(ultimas_sesiones) < 2:
        return
        
    s1 = ultimas_sesiones[0] # Última
    s2 = ultimas_sesiones[1] # Penúltima
    
    if s1.dificultad_percibida is None or s2.dificultad_percibida is None:
        return
        
    cambio_nivel = False
    nuevo_nivel = nivel_actual
    mensaje_nota = ""
    
    # --- REGLA DE ASCENSO ---
    if (s1.puntos >= 800 and s2.puntos >= 800) and (s1.dificultad_percibida <= 2 and s2.dificultad_percibida <= 2):
        if nivel_actual < 5:
            nuevo_nivel = nivel_actual + 1
            cambio_nivel = True
            mensaje_nota = f"🤖 [SISTEMA DDA] Ascenso automático.\nEl paciente demuestra dominio en el área {dominio} (Nivel {nivel_actual}). Rendimiento > 800 pts y carga cognitiva baja en sesiones consecutivas. Se aumenta a Nivel {nuevo_nivel}."

    # --- REGLA DE DESCENSO ---
    elif (s1.puntos <= 300 and s2.puntos <= 300) or (s1.dificultad_percibida == 5 and s2.dificultad_percibida == 5):
        if nivel_actual > 1:
            nuevo_nivel = nivel_actual - 1
            cambio_nivel = True
            mensaje_nota = f"🤖 [SISTEMA DDA] Descenso preventivo.\nAlerta de fatiga en el área {dominio} (Nivel {nivel_actual}). Rendimiento deficiente o frustración reportada ('Muy Difícil'). Se reduce a Nivel {nuevo_nivel} para evitar abandono terapéutico."

    # 3. Aplicar y guardar los cambios
    if cambio_nivel:
        # Asignar el nuevo nivel a la variable correcta de la base de datos
        if dominio == "Cognitivo":
            perfil.nivel_cognitivo = nuevo_nivel
            perfil.nivel_asignado = nuevo_nivel # Actualizamos el global guiándonos por el cognitivo
        elif dominio == "Lenguaje":
            perfil.nivel_lenguaje = nuevo_nivel
        elif dominio == "Motor":
            perfil.nivel_motor = nuevo_nivel
            
        perfil.save()
        
        # Registrar en el Historial Clínico
        try:
            NotaEspecialista.objects.create(
                paciente=perfil,
                medico=perfil.medico_asignado,
                texto=mensaje_nota
            )
        except Exception as e:
            print("Error creando la nota DDA:", e)

@csrf_exempt
def guardar_progreso(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            if hasattr(request.user, 'perfil'):
                perfil = request.user.perfil
            else:
                perfil = PerfilPaciente.objects.get(usuario=request.user)
            
            # Extraemos los datos básicos
            juego_nombre = data.get('juego', data.get('ejercicio', 'Desconocido'))
            nivel = data.get('nivel', 1)
            puntos = data.get('puntos', 0)
            tiempo = data.get('tiempo', 0)
            completado = data.get('completado', True)

            # EXTRAEMOS LOS NUEVOS DATOS SUBJETIVOS
            dificultad = data.get('dificultad_percibida') # Puede ser None
            animo = data.get('estado_animo')              # Puede ser None
            
            # Guardamos en la base de datos incluyendo los nuevos campos
            SesionDeJuego.objects.create(
                paciente=perfil,
                juego=juego_nombre,
                nivel_jugado=nivel,
                puntos=puntos,
                tiempo_jugado=tiempo,
                completado=completado,
                dificultad_percibida=dificultad,
                estado_animo=animo
            )

            # 2. EL ALGORITMO EVALÚA EL RENDIMIENTO Y AJUSTA EL NIVEL (NUEVO)
            evaluar_ajuste_dinamico(perfil, juego_nombre)

            return JsonResponse({'status': 'ok'})
        except Exception as e:
            print(f"❌ Error guardando progreso: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt 
def transcribir_audio(request):
    global MODELO_WHISPER 

    if request.method == 'POST' and request.FILES.get('audio'):
        try:
            if MODELO_WHISPER is None:
                print("⏳ Cargando modelo Whisper por primera vez...")
                MODELO_WHISPER = whisper.load_model("tiny")
                print("✅ Modelo cargado y listo.")

            archivo_audio = request.FILES['audio']
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                for chunk in archivo_audio.chunks():
                    tmp.write(chunk)
                ruta_temporal = tmp.name

            resultado = MODELO_WHISPER.transcribe(ruta_temporal, language="es")
            texto_detectado = resultado["text"]
            
            os.remove(ruta_temporal)
            
            print(f"🎤 Whisper escuchó: {texto_detectado}")
            return JsonResponse({'texto_transcrito': texto_detectado})

        except Exception as e:
            print(f"❌ Error al transcribir: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'No se recibió audio'}, status=400)

@login_required
def analisis_paciente(request, pk):
    perfil_paciente = get_object_or_404(PerfilPaciente, pk=pk)
    sesiones = SesionDeJuego.objects.filter(paciente=perfil_paciente).order_by('fecha')
    
    datos_por_juego = {}
    for sesion in sesiones:
        juego = sesion.juego
        nivel = str(sesion.nivel_jugado)
        
        if juego not in datos_por_juego:
            datos_por_juego[juego] = {}
            
        if nivel not in datos_por_juego[juego]:
            # Añadimos listas para dificultad y ánimo
            datos_por_juego[juego][nivel] = {
                'fechas': [], 
                'puntos': [], 
                'tiempos': [],
                'dificultades': [], 
                'animos': []
            }
            
        datos_por_juego[juego][nivel]['fechas'].append(sesion.fecha.strftime("%d/%m"))
        datos_por_juego[juego][nivel]['puntos'].append(sesion.puntos)
        datos_por_juego[juego][nivel]['tiempos'].append(sesion.tiempo_jugado)
        # Guardamos el dato subjetivo (si es None, mandamos 0 para no romper la gráfica)
        datos_por_juego[juego][nivel]['dificultades'].append(sesion.dificultad_percibida or 0)
        datos_por_juego[juego][nivel]['animos'].append(sesion.estado_animo or 0)

    context = {
        'paciente': perfil_paciente,
        'datos_juegos_json': json.dumps(datos_por_juego)
    }
    return render(request, 'core/patients/analisis_paciente.html', context)