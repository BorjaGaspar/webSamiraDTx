#  WebSamira (Prueba_1)

Proyecto para la gestión y visualización de datos de wearables, desarrollado en Python/Django y preparado para su implementación con Docker.

##  Requisitos

* Windows 10/11
* [Git](https://git-scm.com/)
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Opcional, para despliegue rápido)
* Python 3.10+ (Si se ejecuta manualmente)

##  Instalación

### 1. Clonar el repositorio


```bash
git clone [https://github.com/BorjaGaspar/webSamiraDTx.git](https://github.com/BorjaGaspar/webSamiraDTx.git)
cd webSamiraDTx
```
### 2. Opción A: Ejecución con Docker


Si tienes Docker instalado, levanta todo el entorno con un solo comando:
```bash
docker-compose up --build
```
Importante: La primera vez que levantes el contenedor, debes sincronizar la base de datos ejecutando en otra terminal
```bash
python manage.py migrate
```

La web estará disponible en: http://localhost:8000

### 3. Opción B: Ejecución Manual (Entorno Virtual)

Si prefieres usar el método clásico sin contenedores:

Crear y activar entorno:

```bash
python -m venv venv
.\venv\Scripts\activate
```
Instalar dependencias:
```bash
pip install -r requirements.txt
```
Ejecutar servidor:
```bash
python manage.py runserver
```
## Estructura del Proyecto
* config/: Configuración global de Django.
* core/: Aplicación principal (Vistas públicas y privadas).
* requirements.txt: Dependencias.
* Dockerfile & docker-compose.yml: Configuración Docker.