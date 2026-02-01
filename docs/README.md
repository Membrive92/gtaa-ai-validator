# Documentación del Proyecto gTAA AI Validator

Este directorio contiene documentación técnica detallada sobre el proyecto.

## Documentos Disponibles

### [PHASE1_FLOW_DIAGRAMS.md](PHASE1_FLOW_DIAGRAMS.md)

Diagramas de flujo de la Fase 1: Fundación del Proyecto y CLI.

**Contenido**:
- Estructura del proyecto y paquete Python
- Flujo del CLI con Click (`__main__.py`)
- Descubrimiento recursivo de archivos con exclusiones
- Diagrama de interacción entre componentes
- Decisiones de diseño de la Fase 1 (Click, estructura anticipada)

**Conceptos explicados**:
- Click como framework CLI declarativo
- Descubrimiento de archivos con `rglob` y filtrado
- Estructura de paquete Python ejecutable (`__main__.py`)

### [PHASE2_FLOW_DIAGRAMS.md](PHASE2_FLOW_DIAGRAMS.md)

Diagramas de flujo completos que explican el funcionamiento de la Fase 2: Motor de Análisis Estático.

**Contenido**:
- Diagrama de flujo principal (vista general)
- Subdiagrama: DefinitionChecker.check() - El corazón del análisis
- Subdiagrama: BrowserAPICallVisitor - Recorrido del AST
- Subdiagrama: _get_object_name() - Extraer nombre del objeto
- Subdiagrama: Creación de Violation
- Subdiagrama: Cálculo de Score
- Diagrama de datos - Transformación de estructuras
- Diagrama de interacción entre clases
- Ejemplo concreto paso a paso

**Para quién**:
- Desarrolladores que quieran entender el código
- Evaluadores del TFM
- Estudiantes aprendiendo sobre AST y análisis estático
- Colaboradores del proyecto

**Conceptos explicados**:
- AST (Abstract Syntax Tree)
- Visitor Pattern
- Strategy Pattern
- Facade Pattern
- Dataclasses en Python

### [PHASE3_FLOW_DIAGRAMS.md](PHASE3_FLOW_DIAGRAMS.md)

Diagramas de flujo de la Fase 3: Cobertura Completa de Análisis Estático (9 tipos de violaciones).

**Contenido**:
- Visión general de la arquitectura con 4 checkers
- Flujo principal actualizado con project-level checks
- Check a dos niveles: proyecto vs archivo
- StructureChecker — validación de estructura de directorios
- AdaptationChecker — 4 sub-checks con AST visitors
- QualityChecker — datos hardcoded, funciones largas, naming
- Mapa completo de AST Visitors (4 visitors)
- Flujo de detección de locators duplicados (estado cross-file)
- Mapa de las 9 violaciones con técnicas de detección
- Diagrama de interacción/secuencia entre componentes

**Conceptos nuevos explicados**:
- check_project() — checks a nivel de proyecto
- Cross-file state (locator registry)
- Regex + AST combinados para detección de datos
- Múltiples visitors especializados por tipo de violación

### [PHASE4_FLOW_DIAGRAMS.md](PHASE4_FLOW_DIAGRAMS.md)

Diagramas de flujo de la Fase 4: Reportes HTML/JSON Profesionales.

**Contenido**:
- Arquitectura del módulo de reportes (`reporters/`)
- Flujo de generación de reportes (JSON y HTML)
- JsonReporter — serialización con `to_dict()` + `json.dumps()`
- HtmlReporter — dashboard visual autocontenido
- Estructura del dashboard HTML (secciones, tarjetas, tablas)
- SVG inline: gauge circular de score y gráfico de barras
- Agrupación de violaciones por checker
- Integración con el CLI (`--json`, `--html`)
- Mapa completo de tests (21 unitarios + 4 integración)

**Conceptos nuevos explicados**:
- SVG programático (stroke-dasharray para gauges)
- HTML autocontenido sin dependencias externas
- Prevención XSS con `html.escape()`
- CSS Grid responsive para dashboard

### [PHASE5_FLOW_DIAGRAMS.md](PHASE5_FLOW_DIAGRAMS.md)

Diagramas de flujo de la Fase 5: Análisis Semántico con Inteligencia Artificial.

**Contenido**:
- Arquitectura del módulo LLM (`llm/`)
- Flujo de selección de cliente LLM (Gemini vs Mock)
- GeminiLLMClient — comunicación con Gemini Flash API
- MockLLMClient — heurísticas deterministas (AST + regex)
- Prompt engineering: system prompt, analyze prompt, enrich prompt
- SemanticAnalyzer — orquestación de las dos fases
- Fase 1: detección de violaciones semánticas
- Fase 2: enriquecimiento con sugerencias AI contextuales
- Parsing robusto de respuestas LLM (JSON, markdown, errores)
- Mapa de 13 violaciones de Fase 5 (9 estáticas + 4 semánticas)
- Configuración de API key con .env y python-dotenv
- Mapa de tests (12 tests unitarios para GeminiLLMClient)

**Conceptos nuevos explicados**:
- LLM como herramienta de análisis de código
- Prompt engineering para detección de violaciones
- Duck typing como alternativa a ABC
- Manejo silencioso de errores de API (degradación elegante)
- google-genai SDK nativo
- Configuración por variable de entorno con .env

### [PHASE6_FLOW_DIAGRAMS.md](PHASE6_FLOW_DIAGRAMS.md)

Diagramas de flujo de la Fase 6: Ampliación de Cobertura de Violaciones (13 → 18).

**Contenido**:
- 5 nuevas violaciones basadas en catálogo ISTQB CT-TAE
- 3 violaciones estáticas nuevas en QualityChecker (AST + regex)
- 2 violaciones semánticas nuevas (LLM + MockLLM)
- Ampliación del MockLLMClient con 2 heurísticas
- Ampliación del GeminiLLMClient (VALID_TYPES) y prompts
- Mapa completo de 18 violaciones por capa gTAA
- Mapa de 25 tests nuevos (234 total)
- Consideraciones sobre falsos positivos (Playwright, API testing)

**Conceptos nuevos explicados**:
- Detección de excepciones genéricas con ast.ExceptHandler
- Regex compiladas como constantes de clase
- Detección de estado mutable a dos niveles (módulo + global)
- Ampliación de prompts LLM vs prompts separados
- Análisis de falsos positivos por framework

### [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md)

Registro de decisiones arquitectónicas (ADR) que explica **por qué** se eligió cada enfoque técnico.

**Contenido**:
1. Análisis de código: AST frente a alternativas (mapas anidados, regex)
2. Recorrido del AST: Patrón Visitor
3. Organización de checkers: Patrón Strategy (interfaz uniforme, justificación)
4. Orquestación: Patrón Facade (StaticAnalyzer)
5. Modelos de datos: Dataclasses y Enums
6. Verificación a dos niveles (proyecto + archivo)
7. Optimización: parseo único del AST por archivo
8. Paradigmas de programación utilizados (POO + Declarativo)
9. Reportes: HTML autocontenido frente a alternativas (Jinja2, Chart.js, PDF)
10. Reportes: JSON con serialización propia frente a librerías (Pydantic, marshmallow)
11. CLI: flags separados frente a formato único
12. LLM: Evaluación de APIs y modelos LLM (Claude, GPT-4o, DeepSeek, Gemini, Llama)
13. LLM: SDK google-genai frente a alternativas (openai, REST)
14. LLM: Duck typing frente a clase base abstracta
15. LLM: Manejo silencioso de errores de API
16. LLM: Configuración por variable de entorno frente a alternativas
17. Detección de excepciones genéricas: AST frente a regex
18. Detección de configuración hardcodeada: regex compiladas como constantes de clase
19. Detección de estado mutable compartido: dos fases complementarias
20. Ampliación de violaciones semánticas: prompts ampliados frente a prompts separados
21. Heurísticas mock: búsqueda textual frente a visitor AST para detección de asserts

**Para quién**:
- Evaluadores del TFM que quieran entender las decisiones de diseño
- Desarrolladores que consideren alternativas
- Estudiantes aprendiendo sobre patrones de diseño aplicados

---

## Documentación Futura (Planeada)

### PHASE7_FLOW_DIAGRAMS.md (Fase 7)
Diagramas de flujo de la Fase 7: Soporte para proyectos con API testing.
- Clasificador de archivos (API vs UI tests)
- Configuración por proyecto (.gtaa.yaml)
- Reglas condicionales por tipo de test
- Reducción de falsos positivos

### PHASE8_FLOW_DIAGRAMS.md (Fase 8)
Diagramas de flujo de la Fase 8: Optimización y documentación final.
- Optimización de prompts LLM
- Integración CI/CD
- Documentación TFM final

### gtaa_reference.md
Referencia completa de la arquitectura gTAA según ISTQB CT-TAE.

### api_documentation.md
Documentación de la API pública del validador para uso programático.

### contributing.md
Guía para contribuir al proyecto (estructura de código, estándares, pull requests).

---

## Cómo Usar Esta Documentación

### Para Aprender
1. Lee [PHASE1_FLOW_DIAGRAMS.md](PHASE1_FLOW_DIAGRAMS.md) para entender la estructura base y el CLI
2. Lee [PHASE2_FLOW_DIAGRAMS.md](PHASE2_FLOW_DIAGRAMS.md) para entender el motor de análisis estático
3. Lee [PHASE3_FLOW_DIAGRAMS.md](PHASE3_FLOW_DIAGRAMS.md) para la cobertura completa de 9 violaciones
4. Lee [PHASE4_FLOW_DIAGRAMS.md](PHASE4_FLOW_DIAGRAMS.md) para los reportes HTML/JSON
5. Lee [PHASE5_FLOW_DIAGRAMS.md](PHASE5_FLOW_DIAGRAMS.md) para el análisis semántico con AI
6. Lee [PHASE6_FLOW_DIAGRAMS.md](PHASE6_FLOW_DIAGRAMS.md) para la ampliación a 18 violaciones
7. Lee [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) para las justificaciones técnicas
8. Ejecuta el código mientras lees: `python -m gtaa_validator examples/bad_project --ai --verbose`

### Para Desarrollar
1. Consulta [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) para entender los patrones (Strategy, Visitor, Facade)
2. Consulta los diagramas de interacción entre clases en los documentos de flujo
3. Sigue la misma estructura de `BaseChecker` para añadir nuevos checkers

### Para Evaluar (TFM)
1. Los diagramas demuestran comprensión técnica profunda
2. [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) documenta las decisiones de diseño y sus alternativas evaluadas
3. Muestran aplicación correcta de patrones de diseño y paradigmas
4. Facilitan la reproducibilidad de resultados

---

## Convenciones de Documentación

### Diagramas ASCII
- Usamos diagramas ASCII para compatibilidad universal
- Pueden visualizarse en cualquier editor de texto
- Fáciles de versionar con Git
- No requieren software especializado

### Formato Markdown
- Todo está en Markdown para fácil lectura
- Compatible con GitHub, GitLab, VSCode
- Puede convertirse a PDF/HTML si es necesario

### Enlaces Internos
- Los enlaces apuntan a líneas específicas del código
- Formato: `archivo.py:línea_inicial-línea_final`
- Facilita navegar entre documentación y código

---

## Actualizaciones

Este directorio se actualizará con:
- Diagramas de nuevas fases
- Documentación de nuevas características
- Guías de uso avanzadas
- Ejemplos adicionales

**Última actualización**: 1 Febrero 2026
