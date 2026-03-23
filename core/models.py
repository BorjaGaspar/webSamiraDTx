from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone 

# ================================================================
# TABLA 1: PERFIL DEL PACIENTE
# ================================================================
class PerfilPaciente(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    
    # --- DATOS GENERALES ---
    es_medico = models.BooleanField(default=False, verbose_name="¿Es Médico?")
    medico_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pacientes_supervisados')
    lugar_habitual = models.CharField(max_length=100, blank=True, null=True, verbose_name="Lugar Habitual (Ej. Casa, Hospital)")
    ciudad_residencia = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ciudad de Residencia")
    anios_estudio = models.IntegerField(null=True, blank=True, verbose_name="Años de escolarización")
    
    # --- DATOS FÍSICOS ---
    edad = models.IntegerField(null=True, blank=True)
    altura = models.IntegerField(null=True, blank=True)
    peso = models.IntegerField(null=True, blank=True)
    
    OPCIONES_LADO = [
        ('Izquierdo', 'Lado Izquierdo'),
        ('Derecho', 'Lado Derecho'),
        ('Ambos', 'Ambos Lados'),
        ('Ninguno', 'Sin afectación motora'),
    ]
    
    lado_afectado = models.CharField(max_length=20, choices=OPCIONES_LADO, null=True, blank=True)
    
    # --- ESTADO DE EVALUACIÓN ---
    test_completado = models.BooleanField(default=False)
    fecha_ultima_evaluacion = models.DateTimeField(null=True, blank=True)
    
    # --- NIVELES ESPECÍFICOS (NUEVO SISTEMA) ---
    # Nivel Global (Mantenemos por compatibilidad, pero usaremos los de abajo)
    nivel_asignado = models.IntegerField(default=1, verbose_name="Nivel Global (Legacy)")
    
    # Los 3 Pilares de la Terapia
    nivel_cognitivo = models.IntegerField(default=1, verbose_name="Nivel Cognitivo (1-5)")
    nivel_lenguaje = models.IntegerField(default=1, verbose_name="Nivel Lenguaje (1-5)")
    nivel_motor = models.IntegerField(default=1, verbose_name="Nivel Motor (1-5)")

    # Puntuaciones MoCA
    puntuacion_total_moca = models.IntegerField(default=0, verbose_name="MoCA Total (0-30)")
    
    # Desglose MoCA
    score_visuoespacial = models.IntegerField(default=0, verbose_name="Visuoespacial/Ejecutiva")
    score_identificacion = models.IntegerField(default=0, verbose_name="Identificación")
    score_atencion = models.IntegerField(default=0, verbose_name="Atención")
    score_lenguaje = models.IntegerField(default=0, verbose_name="Lenguaje")
    score_abstraccion = models.IntegerField(default=0, verbose_name="Abstracción")
    score_recuerdo = models.IntegerField(default=0, verbose_name="Recuerdo Diferido")
    score_orientacion = models.IntegerField(default=0, verbose_name="Orientación")
    # --- GAMIFICACIÓN ---
    racha_dias = models.IntegerField(default=0)
    dias_totales = models.IntegerField(default=0)
    puntos_totales = models.IntegerField(default=0)
    tiempo_terapia_hoy = models.IntegerField(default=0)
    
    telefono = models.CharField(max_length=15, blank=True, null=True)

    #Enseñar a la tabla PerfilPaciente a que mire en EvaluacionMOCA si el medico ha revisado ya o no el test MOca
    @property
    def tiene_moca_pendiente(self):
        # Busca si este paciente tiene alguna evaluación donde revisada_por_medico sea False
        return self.evaluaciones_moca.filter(revisada_por_medico=False).exists()

    def __str__(self):
        return f"{self.usuario.username} ({'Médico' if self.es_medico else 'Paciente'})"


# ================================================================
# TABLA 2: HISTORIAL DE SESIONES
# ================================================================
class SesionDeJuego(models.Model):
    paciente = models.ForeignKey(PerfilPaciente, on_delete=models.CASCADE, related_name='sesiones')
    juego = models.CharField(max_length=100, default="General")
    fecha = models.DateTimeField(default=timezone.now, verbose_name="Fecha UTC")
    puntos = models.IntegerField(default=0)
    nivel_jugado = models.IntegerField(default=1)
    tiempo_jugado = models.IntegerField(default=0, verbose_name="Segundos")
    completado = models.BooleanField(default=True)
    
    # --- NUEVOS CAMPOS DE AUTOPERCEPCIÓN (Escala 1-5) ---
    dificultad_percibida = models.IntegerField(null=True, blank=True)
    estado_animo = models.IntegerField(null=True, blank=True)
    
    detalles = models.TextField(blank=True, null=True, verbose_name="Detalles JSON")

    def __str__(self):
        return f"{self.paciente.usuario.username} - {self.juego} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        ordering = ['-fecha']

# ================================================================
# TABLA 3: NOTAS DEL ESPECIALISTA (HISTORIAL CLÍNICO)
# ================================================================
class NotaEspecialista(models.Model):
    paciente = models.ForeignKey(PerfilPaciente, on_delete=models.CASCADE, related_name='notas')
    medico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='notas_escritas')
    texto = models.TextField(verbose_name="Contenido de la nota")
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fecha'] # Esto hace que se ordenen automáticamente de más nueva a más antigua

    def __str__(self):
        return f"Nota para {self.paciente.usuario.username} - {self.fecha.strftime('%d/%m/%Y')}"

# ================================================================
# TABLA 4: HISTORIAL DE EVALUACIONES MOCA (STORE & FORWARD)
# ================================================================
class EvaluacionMoCA(models.Model):
    paciente = models.ForeignKey(PerfilPaciente, on_delete=models.CASCADE, related_name='evaluaciones_moca')
    fecha_evaluacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de realización")
    revisada_por_medico = models.BooleanField(default=False, verbose_name="Revisada por el Médico")

    # --- PUNTUACIONES PRINCIPALES (Los 7 dominios) ---
    score_visuoespacial = models.IntegerField(default=0)
    score_identificacion = models.IntegerField(default=0)
    score_atencion = models.IntegerField(default=0)
    score_lenguaje = models.IntegerField(default=0)
    score_abstraccion = models.IntegerField(default=0)
    score_recuerdo = models.IntegerField(default=0)
    score_orientacion = models.IntegerField(default=0)
    score_total = models.IntegerField(default=0, verbose_name="Nota Final (0-30)")

    # --- AUDITORÍA CLÍNICA: ARCHIVOS MULTIMEDIA (Base64) ---
    # Usamos TextField porque las cadenas Base64 de imágenes y audios son inmensas
    dibujo_cubo_b64 = models.TextField(blank=True, null=True)
    dibujo_reloj_b64 = models.TextField(blank=True, null=True)
    audio_frase1_b64 = models.TextField(blank=True, null=True)
    audio_frase2_b64 = models.TextField(blank=True, null=True)
    audio_fluidez_b64 = models.TextField(blank=True, null=True)
    audio_tren_b64 = models.TextField(blank=True, null=True)
    audio_reloj_b64 = models.TextField(blank=True, null=True)
    audio_recuerdo_b64 = models.TextField(blank=True, null=True)

    # --- AUDITORÍA CLÍNICA: TRANSCRIPCIONES IA Y TEXTOS ---
    transcripcion_frase1 = models.TextField(blank=True, null=True)
    transcripcion_frase2 = models.TextField(blank=True, null=True)
    transcripcion_fluidez = models.TextField(blank=True, null=True)
    abstraccion_tren_respuesta = models.TextField(blank=True, null=True)
    abstraccion_reloj_respuesta = models.TextField(blank=True, null=True)
    transcripcion_recuerdo = models.TextField(blank=True, null=True)

    # --- RESPALDO DE SEGURIDAD (RAW DATA) ---
    # Aquí guardaremos el objeto JavaScript íntegro para conservar los sub-intentos y tiempos
    datos_completos_raw = models.JSONField(blank=True, null=True, verbose_name="JSON Íntegro del Frontend")

    class Meta:
        ordering = ['-fecha_evaluacion'] # Ordena de más reciente a más antiguo

    def __str__(self):
        return f"MoCA | {self.paciente.usuario.username} | Puntuación: {self.score_total}/30 | {self.fecha_evaluacion.strftime('%d/%m/%Y')}"

# ================================================================
# TABLA 5: BUZÓN CLÍNICO (NOTIFICACIONES)
# ================================================================
class NotificacionBuzon(models.Model):
    TIPO_REMITENTE = [
        ('SISTEMA', 'Sistema SamiraDTx'),
        ('MEDICO', 'Especialista Médico'),
    ]
    paciente = models.ForeignKey(PerfilPaciente, on_delete=models.CASCADE, related_name='notificaciones')
    remitente = models.CharField(max_length=20, choices=TIPO_REMITENTE, default='SISTEMA')
    # Guardamos qué médico escribió la nota (si es que fue un médico y no el sistema)
    medico_autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    mensaje = models.TextField(verbose_name="Contenido del mensaje")
    fecha = models.DateTimeField(default=timezone.now)
    leida = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha'] # Las más nuevas arriba

    def __str__(self):
        return f"Notificación para {self.paciente.usuario.username} - {self.remitente}"

    