from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import os
from datetime import datetime
from typing import Dict, Optional, Any, List
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId

# Cargar variables de entorno
load_dotenv()

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

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "UPC")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "alertas2")

# Clase para convertir ObjectId a str en respuestas JSON
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

# Conexión a MongoDB
def get_db():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    try:
        yield db
    finally:
        client.close()

# Para compatibilidad con código existente
CASOS_DIR = Path("./static/data")
CASOS_DIR.mkdir(exist_ok=True, parents=True)
CASOS_FILE = CASOS_DIR / "casos.json"

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
def healthcheck(db = Depends(get_db)):
    """Endpoint para verificar que el servidor esté funcionando correctamente"""
    try:
        # Verificar conexión con MongoDB
        db.command("ping")
        return {"status": "ok", "timestamp": datetime.now().isoformat(), "database": "connected"}
    except Exception as e:
        return {"status": "error", "timestamp": datetime.now().isoformat(), "database": f"disconnected: {str(e)}"}

@app.post("/api/casos")
async def crear_caso(caso: Dict[str, Any] = Body(...), db = Depends(get_db)):
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
        collection = db[COLLECTION_NAME]
        
        # Generar ID único con formato CASO-XXXX
        # Buscar el último ID en la colección
        ultimo_caso = list(collection.find({}, {"id_caso": 1}).sort("id_caso", -1).limit(1))
        
        if ultimo_caso and "id_caso" in ultimo_caso[0]:
            try:
                next_id = int(ultimo_caso[0]["id_caso"].replace("CASO-", "")) + 1
            except (ValueError, AttributeError):
                next_id = 1
        else:
            next_id = 1
            
        caso_id = f"CASO-{next_id:04d}"
        
        # Agregar metadatos
        nuevo_caso = {
            **caso,
            "id_caso": caso_id,
            "fecha_creacion": datetime.now().isoformat(),
            "estado": "Abierto"
        }
        
        # Insertar en MongoDB
        result = collection.insert_one(nuevo_caso)
        
        # Obtener el documento insertado
        inserted_id = result.inserted_id
        inserted_doc = collection.find_one({"_id": inserted_id})
        
        # Convertir ObjectId a string para la respuesta JSON
        if inserted_doc and "_id" in inserted_doc:
            inserted_doc["_id"] = str(inserted_doc["_id"])
            
        return inserted_doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear caso: {str(e)}")

@app.get("/api/casos")
async def get_casos(id_caso: Optional[str] = None, id_alarma: Optional[str] = None, db = Depends(get_db)):
    """Endpoint para obtener todos los casos o filtrar por ID de caso o alarma"""
    try:
        collection = db[COLLECTION_NAME]
        
        # Construir filtro basado en parámetros
        filtro = {}
        if id_caso:
            filtro["id_caso"] = id_caso
        if id_alarma:
            filtro["id_alarma"] = id_alarma
        
        # Ejecutar consulta
        casos = list(collection.find(filtro))
        
        # Convertir ObjectId a string para la respuesta JSON
        for caso in casos:
            caso["_id"] = str(caso["_id"])
            
        return casos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener casos: {str(e)}")

@app.get("/api/casos/{id_caso}")
async def get_caso(id_caso: str, db = Depends(get_db)):
    """Endpoint para obtener un caso específico por su ID"""
    try:
        collection = db[COLLECTION_NAME]
        caso = collection.find_one({"id_caso": id_caso})
        
        if not caso:
            raise HTTPException(status_code=404, detail=f"Caso {id_caso} no encontrado")
        
        # Convertir ObjectId a string para la respuesta JSON
        caso["_id"] = str(caso["_id"])
        
        return caso
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error al obtener caso: {str(e)}")

# Endpoint para obtener todos los informes de la colección "notificacion"
@app.get("/api/informes")
async def get_informes(db = Depends(get_db)):
    """Endpoint para obtener todos los informes almacenados en la colección 'notificacion'"""
    try:
        # Obtener la colección de notificaciones
        collection = db["notificacion"]
        
        # Consultar todos los documentos y convertirlos a formato serializable
        informes = []
        for doc in collection.find():
            # Crear un nuevo diccionario con valores serializables
            informe_serializable = {}
            for key, value in doc.items():
                # Convertir ObjectId a string
                if isinstance(value, ObjectId):
                    informe_serializable[key] = str(value)
                # Manejar otros tipos de datos no serializables si fuera necesario
                else:
                    informe_serializable[key] = value
            
            informes.append(informe_serializable)
        
        return informes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener informes: {str(e)}")

# Nuevo endpoint para migrar datos del archivo JSON a MongoDB (útil para la transición)
@app.post("/api/migrar-datos", status_code=201)
async def migrar_datos(db = Depends(get_db)):
    """Endpoint para migrar datos del archivo JSON a MongoDB"""
    try:
        # Ruta al archivo JSON
        json_path = Path("./static/data/casos.json")
        if not json_path.exists():
            return {"message": "No hay archivo JSON para migrar", "migrados": 0}
        
        # Leer datos del archivo JSON
        with open(json_path, "r") as f:
            casos = json.load(f)
        
        if not casos:
            return {"message": "No hay casos para migrar", "migrados": 0}
        
        # Obtener colección de MongoDB
        collection = db[COLLECTION_NAME]
        
        # Migrar cada caso
        inserted_count = 0
        for caso in casos:
            # Verificar si ya existe
            if collection.find_one({"id_caso": caso.get("id_caso")}):
                continue
                
            # Insertar en MongoDB
            collection.insert_one(caso)
            inserted_count += 1
        
        return {
            "message": "Datos migrados correctamente",
            "migrados": inserted_count,
            "total": len(casos)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al migrar datos: {str(e)}")
