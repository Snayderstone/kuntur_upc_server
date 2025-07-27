#!/bin/bash

# Script simple para construir y publicar imagen Docker
# Uso: ./docker_build_publish.sh [tag_version]

set -e  # Salir si hay error

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker no está instalado"
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker no está ejecutándose"
    exit 1
fi

# Obtener username de Docker Hub
echo "Verificando login en Docker Hub..."
DOCKER_USERNAME=""

# Intentar obtener username actual
if docker info 2>/dev/null | grep -q "Username:"; then
    DOCKER_USERNAME=$(docker info 2>/dev/null | grep "Username:" | awk '{print $2}')
fi

# Si no hay username, hacer login
if [ -z "$DOCKER_USERNAME" ]; then
    echo "Haciendo login en Docker Hub..."
    docker login
    
    # Intentar obtener username después del login
    if docker info 2>/dev/null | grep -q "Username:"; then
        DOCKER_USERNAME=$(docker info 2>/dev/null | grep "Username:" | awk '{print $2}')
    fi
fi

# Si aún no hay username, pedir al usuario
if [ -z "$DOCKER_USERNAME" ]; then
    echo -n "Ingresa tu username de Docker Hub: "
    read DOCKER_USERNAME
fi

if [ -z "$DOCKER_USERNAME" ]; then
    echo "ERROR: No se pudo obtener el username"
    exit 1
fi

echo "Usuario: $DOCKER_USERNAME"

# Definir versión
VERSION="${1:-latest}"

# Nombres de imagen
IMAGE_NAME="$DOCKER_USERNAME/img_kuntur_upc_server"
FULL_IMAGE_NAME="$IMAGE_NAME:$VERSION"

echo "Construyendo imagen: $FULL_IMAGE_NAME"

# Construir imagen
docker build -t "$FULL_IMAGE_NAME" .

if [ $? -ne 0 ]; then
    echo "ERROR: Falló la construcción"
    exit 1
fi

echo "Imagen construida exitosamente"

# Probar la imagen
echo "Probando la imagen..."
docker run --name test-container -p 9000:8050 -d "$FULL_IMAGE_NAME"

# Esperar un poco
sleep 15

# Verificar si el contenedor está corriendo
if ! docker ps | grep -q test-container; then
    echo "ERROR: El contenedor no está corriendo"
    docker logs test-container
    docker rm -f test-container 2>/dev/null
    exit 1
fi

# Probar si responde
echo "Verificando si el servidor responde..."
if curl -s http://localhost:9000 > /dev/null; then
    echo "Servidor responde correctamente"
else
    echo "ADVERTENCIA: El servidor no responde, pero continuando..."
fi

# Limpiar contenedor de prueba
docker rm -f test-container > /dev/null 2>&1

# Subir a Docker Hub
echo "Subiendo imagen a Docker Hub..."
docker push "$FULL_IMAGE_NAME"

if [ $? -ne 0 ]; then
    echo "ERROR: Falló la subida"
    exit 1
fi

echo ""
echo "========================================="
echo "COMPLETADO EXITOSAMENTE"
echo "========================================="
echo "Imagen: $FULL_IMAGE_NAME"
echo ""
echo "Para usar:"
echo "  docker run -p 8050:8050 $FULL_IMAGE_NAME"
echo ""
echo "URLs:"
echo "  http://localhost:8050"
echo "  http://localhost:8050/docs"
echo "  http://localhost:8050/sse"
echo ""
