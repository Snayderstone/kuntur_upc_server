from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Optional, Any

# Inicializar la aplicación FastAPI
app = FastAPI(title="Kuntur Detector API", description="API para la gestión de casos para UPC de Ecuador")

# Configurar CORS para permitir solicitudes del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las origins
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos
    allow_headers=["*"],  # Permite todos los headers
)

# Ya no necesitamos el directorio JS
# JS_DIR = Path("./static/js")
# JS_DIR.mkdir(exist_ok=True, parents=True)

# Directorio para almacenar los casos en formato JSON
CASOS_DIR = Path("./static/data")
CASOS_DIR.mkdir(exist_ok=True, parents=True)
CASOS_FILE = CASOS_DIR / "casos.json"

# Inicializar archivo de casos si no existe
if not CASOS_FILE.exists():
    with open(CASOS_FILE, "w") as f:
        json.dump([], f)

# Ubicación fija de una UPC en Quito (se mantiene por si se necesita para los casos)
UPC_QUITO = {
    "name": "UPC Centro Histórico",
    "latitude": -0.2201641,
    "longitude": -78.4832264
}

@app.get("/")
async def home():
    """Página principal con documentación del API"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Kuntur Detector API</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }
            h1 { color: #333; }
            h2 { color: #444; margin-top: 20px; }
            .endpoint { border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .method { font-weight: bold; color: #008000; }
            .path { font-family: monospace; }
            .note { background-color: #f8f9fa; padding: 10px; border-left: 4px solid #007bff; margin: 15px 0; }
        </style>
    </head>
    <body>
        <h1>Kuntur Detector API</h1>
        <p>API para la gestión de casos de UPC Ecuador - Versión 1.0</p>
        
        <div class="note">
            <p><strong>Nota:</strong> Esta API tiene habilitado CORS para permitir solicitudes desde cualquier origen, 
            lo que facilita la integración con frameworks frontend como React Native.</p>
        </div>
        
        <h2>Endpoints disponibles:</h2>
        
        <div class="endpoint">
            <p><span class="method">GET</span> <span class="path">/</span></p>
            <p>Documentación del API</p>
        </div>
        
        <div class="endpoint">
            <p><span class="method">GET</span> <span class="path">/healthcheck</span></p>
            <p>Verificar estado del servidor</p>
            <p>Respuesta: <code>{"status": "ok", "timestamp": "2025-07-23T10:30:15.123456"}</code></p>
        </div>
        
        <div class="endpoint">
            <p><span class="method">POST</span> <span class="path">/api/casos</span></p>
            <p>Crear un nuevo caso</p>
            <p>Campos requeridos:</p>
            <ul>
                <li><code>id_alarma</code>: ID de la alerta asociada</li>
                <li><code>nombre_agente</code>: Nombre del agente que registra el caso</li>
                <li><code>cedula_agente</code>: Cédula del agente</li>
                <li><code>nombre_victima</code>: Nombre de la víctima</li>
                <li><code>cedula_victima</code>: Cédula de la víctima</li>
                <li><code>informe_policial</code>: Descripción del caso</li>
            </ul>
        </div>
        
        <div class="endpoint">
            <p><span class="method">GET</span> <span class="path">/api/casos</span></p>
            <p>Obtener lista de casos con filtros opcionales</p>
            <p>Query params: <code>id_caso</code>, <code>id_alarma</code> (ambos opcionales)</p>
        </div>
        
        <div class="endpoint">
            <p><span class="method">GET</span> <span class="path">/api/casos/{id_caso}</span></p>
            <p>Obtener un caso específico por su ID</p>
        </div>
        
        <h2>Ejemplos de uso:</h2>
        
        <pre><code>// Obtener todos los casos
fetch('http://0.0.0.0:8050/api/casos')
  .then(response => response.json())
  .then(data => console.log(data));</code></pre>
        
        <pre><code>// Crear un nuevo caso
fetch('http://0.0.0.0:8050/api/casos', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    id_alarma: 'AL23072504',
    nombre_agente: 'Juan Pérez',
    cedula_agente: '1723456789',
    nombre_victima: 'María López',
    cedula_victima: '1712345678',
    informe_policial: 'Descripción del caso'
  })
})
  .then(response => response.json())
  .then(data => console.log(data));</code></pre>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@app.get("/healthcheck")
def healthcheck():
    """Endpoint para verificar que el servidor esté funcionando correctamente"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/api/casos")
async def crear_caso(caso: Dict[str, Any] = Body(...)):
    """Endpoint para crear un nuevo caso en la base de datos"""
    required_fields = ['id_alarma', 'nombre_agente', 'cedula_agente', 
                     'nombre_victima', 'cedula_victima', 'informe_policial']
    
    # Validar campos requeridos
    missing_fields = [field for field in required_fields if field not in caso]
    if missing_fields:
        raise HTTPException(
            status_code=400, 
            detail=f"Campos requeridos faltantes: {', '.join(missing_fields)}"
        )
    
    try:
        # Cargar casos existentes
        casos = []
        if CASOS_FILE.exists():
            with open(CASOS_FILE, "r") as f:
                try:
                    casos = json.load(f)
                except json.JSONDecodeError:
                    casos = []
        
        # Generar ID único con formato CASO-XXXX
        next_id = 1
        if casos:
            max_id = max([int(caso["id_caso"].replace("CASO-", "")) for caso in casos if "id_caso" in caso])
            next_id = max_id + 1
            
        caso_id = f"CASO-{next_id:04d}"
        
        # Agregar metadatos
        nuevo_caso = {
            **caso,
            "id_caso": caso_id,
            "fecha_creacion": datetime.now().isoformat(),
            "estado": "Abierto"
        }
        
        # Agregar a la lista y guardar
        casos.append(nuevo_caso)
        with open(CASOS_FILE, "w") as f:
            json.dump(casos, f, indent=2)
            
        return nuevo_caso
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear caso: {str(e)}")

@app.get("/api/casos")
async def get_casos(id_caso: Optional[str] = None, id_alarma: Optional[str] = None):
    """Endpoint para obtener todos los casos o filtrar por ID de caso o alarma"""
    try:
        if not CASOS_FILE.exists():
            return []
            
        with open(CASOS_FILE, "r") as f:
            try:
                casos = json.load(f)
            except json.JSONDecodeError:
                return []
                
        # Aplicar filtros si se especifican
        if id_caso:
            casos = [caso for caso in casos if caso.get("id_caso") == id_caso]
        if id_alarma:
            casos = [caso for caso in casos if caso.get("id_alarma") == id_alarma]
            
        return casos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener casos: {str(e)}")

@app.get("/api/casos/{id_caso}")
async def get_caso(id_caso: str):
    """Endpoint para obtener un caso específico por su ID"""
    try:
        casos = await get_casos(id_caso=id_caso)
        if not casos:
            raise HTTPException(status_code=404, detail=f"Caso {id_caso} no encontrado")
        return casos[0]
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error al obtener caso: {str(e)}")
