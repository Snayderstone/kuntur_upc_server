# Kuntur Detector API

API para la gestión de casos de seguridad de las Unidades de Policía Comunitaria (UPC) de Ecuador.

## Descripción

Este sistema proporciona una API para registrar y gestionar casos relacionados con alertas de seguridad. 
La API permite crear nuevos casos, obtener listados de casos existentes y consultar casos específicos por su ID.

## Características

- API RESTful para la gestión de casos
- Endpoints para crear y consultar casos
- Verificación de estado del servidor
- Soporte CORS para integración con aplicaciones frontend (React Native)
- Almacenamiento persistente de datos en archivos JSON

## Requisitos

- Python 3.13+
- FastAPI
- Las dependencias se manejan con `uv`

## Instalación

```bash
# Instalar dependencias
uv add fastapi uvicorn
```

## Ejecución

```bash
# Iniciar el servidor de desarrollo
uv run main.py
```

El servidor se ejecutará en `http://localhost:8050` por defecto.

## Estructura del proyecto

```
kuntur_upc_server/
│
├── app/
│   ├── __init__.py
│   └── server.py           # API FastAPI
│
├── static/
│   ├── data/               # Almacenamiento de casos en formato JSON
│   ├── img/                # Imágenes utilizadas por la API
│   └── js/                 # Código JavaScript para consumir la API
│
├── main.py                 # Punto de entrada
├── pyproject.toml          # Configuración del proyecto
└── README.md
```

## Endpoints de la API

### GET /
Muestra la documentación de la API

### GET /healthcheck
Verifica el estado del servidor
- Respuesta: `{"status": "ok", "timestamp": "2025-07-23T10:30:15.123456"}`

### POST /api/casos
Crea un nuevo caso en la base de datos
- Campos requeridos:
  - `id_alarma`: ID de la alerta asociada
  - `nombre_agente`: Nombre del agente que registra el caso
  - `cedula_agente`: Cédula del agente
  - `nombre_victima`: Nombre de la víctima
  - `cedula_victima`: Cédula de la víctima
  - `informe_policial`: Descripción del caso

### GET /api/casos
Obtiene la lista de casos, opcionalmente filtrados
- Parámetros de consulta (opcionales):
  - `id_caso`: Filtrar por ID específico de caso
  - `id_alarma`: Filtrar por ID específico de alarma

### GET /api/casos/{id_caso}
Obtiene un caso específico por su ID
- Parámetros de ruta:
  - `id_caso`: ID del caso a consultar