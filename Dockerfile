# =============================================================================
# gTAA AI Validator — Imagen Docker
# Construcción multistage: etapa build (wheels) + etapa runtime (slim)
#
# Uso:
#   docker build -t gtaa-validator .
#   docker run -v ./mi-proyecto:/project gtaa-validator
#   docker run -v ./mi-proyecto:/project gtaa-validator . --verbose --ai --provider mock
#   docker run -e GEMINI_API_KEY=key -v ./mi-proyecto:/project gtaa-validator . --ai
# =============================================================================

# --- Etapa 1: Construir wheels ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Instalar herramientas de compilacion (necesarias para tree-sitter)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar herramientas de build Python
RUN pip install --no-cache-dir build wheel

# Copiar ficheros de packaging (cache de capas Docker)
COPY pyproject.toml setup.py README.md ./

# Copiar codigo fuente del paquete
COPY gtaa_validator/ ./gtaa_validator/

# Construir wheels del proyecto y todas las dependencias
RUN pip wheel --no-cache-dir --wheel-dir /wheels ".[all]"

# --- Etapa 2: Imagen de ejecucion ---
FROM python:3.12-slim

LABEL maintainer="Jose Antonio Membrive Guillen <membri_2@hotmail.com>"
LABEL org.opencontainers.image.description="Validador de cumplimiento arquitectonico gTAA (ISTQB CT-TAE)"
LABEL org.opencontainers.image.source="https://github.com/Membrive92/gtaa-ai-validator"
LABEL org.opencontainers.image.licenses="MIT"

# Instalar wheels sin cache ni herramientas de build
COPY --from=builder /wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/* && rm -rf /tmp/wheels

# Variable de entorno para API key de Gemini (pasar en runtime con -e)
ENV GEMINI_API_KEY=""

# Crear usuario sin privilegios (SEC-06: principio de minimo privilegio)
RUN useradd --create-home --shell /bin/bash validator
USER validator

# Directorio de trabajo donde se monta el proyecto del usuario
WORKDIR /project

# Entry point: comando gtaa-validator (definido en pyproject.toml [project.scripts])
ENTRYPOINT ["gtaa-validator"]

# Argumento por defecto: analizar directorio actual (/project = volumen montado)
CMD ["."]
