FROM python:3.13-alpine

# Instalar dependencias necesarias para compilación
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    curl \
    && pip install --no-cache-dir uv \
    && apk del .build-deps \
    && apk add --no-cache curl

# Set the working directory
WORKDIR /app

# Copy the entire project for installation
COPY . .

# Install dependencies using uv sync
RUN uv sync

# Expose the port for SSE server
EXPOSE 8050

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8050/ || exit 1

# Entrypoint to start the SSE server using uv run
CMD ["uv", "run", "main.py", "--host", "0.0.0.0", "--port", "8050"]