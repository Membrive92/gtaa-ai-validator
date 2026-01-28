# Documentación del Proyecto gTAA AI Validator

Este directorio contiene documentación técnica detallada sobre el proyecto.

## Documentos Disponibles

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

### [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md)

Registro de decisiones arquitectónicas (ADR) que explica **por qué** se eligió cada enfoque técnico.

**Contenido**:
- Por qué AST y no mapas anidados ni regex puro
- Por qué Visitor Pattern y no bucles con ast.walk()
- Por qué Strategy Pattern (BaseChecker) y no un checker monolítico
- Por qué Facade (StaticAnalyzer) y no llamadas directas
- Por qué Dataclasses + Enums y no diccionarios
- Por qué checks a dos niveles (proyecto + archivo)

**Para quién**:
- Evaluadores del TFM que quieran entender las decisiones de diseño
- Desarrolladores que consideren alternativas
- Estudiantes aprendiendo sobre patrones de diseño aplicados

---

## Documentación Futura (Planeada)

### gtaa_reference.md (Fase 3+)
Referencia completa de la arquitectura gTAA según ISTQB CT-TAE.

### api_documentation.md (Fase 4+)
Documentación de la API pública del validador para uso programático.

### contributing.md
Guía para contribuir al proyecto (estructura de código, estándares, pull requests).

### architecture_decisions.md
Registro de decisiones arquitectónicas importantes (ADR - Architecture Decision Records).

---

## Cómo Usar Esta Documentación

### Para Aprender
1. Lee [PHASE2_FLOW_DIAGRAMS.md](PHASE2_FLOW_DIAGRAMS.md) siguiendo el orden de los diagramas
2. Ejecuta el código mientras lees: `python -m gtaa_validator examples/bad_project --verbose`
3. Compara el output con los diagramas para entender el flujo

### Para Desarrollar
1. Consulta los diagramas de interacción entre clases
2. Revisa los patrones de diseño utilizados
3. Sigue la misma estructura para añadir nuevos checkers en Fase 3

### Para Evaluar (TFM)
1. Los diagramas demuestran comprensión técnica profunda
2. Muestran aplicación correcta de patrones de diseño
3. Documentan decisiones de implementación
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

**Última actualización**: 28 Enero 2026
