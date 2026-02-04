# Decisiones Arquitectónicas — gTAA AI Validator

## Propósito de este documento

Este documento recoge las decisiones arquitectónicas tomadas durante el desarrollo del proyecto gTAA AI Validator. Para cada decisión se documenta el problema que resuelve, las alternativas evaluadas, la solución elegida y la justificación técnica.

El formato sigue la estructura de un ADR (Architecture Decision Record) adaptado para el contexto académico del TFM.

---

## Índice

1. [Análisis de código: AST frente a alternativas](#1-análisis-de-código-ast-frente-a-alternativas)
2. [Recorrido del AST: Patrón Visitor](#2-recorrido-del-ast-patrón-visitor)
3. [Organización de checkers: Patrón Strategy](#3-organización-de-checkers-patrón-strategy)
4. [Orquestación: Patrón Facade](#4-orquestación-patrón-facade)
5. [Modelos de datos: Dataclasses y Enums](#5-modelos-de-datos-dataclasses-y-enums)
6. [Verificación a dos niveles: proyecto y archivo](#6-verificación-a-dos-niveles-proyecto-y-archivo)
7. [Optimización: parseo único del AST por archivo](#7-optimización-parseo-único-del-ast-por-archivo)
8. [Paradigmas de programación utilizados](#8-paradigmas-de-programación-utilizados)
9. [Reportes: HTML autocontenido frente a alternativas](#9-reportes-html-autocontenido-frente-a-alternativas)
10. [Reportes: JSON con serialización propia frente a librerías](#10-reportes-json-con-serialización-propia-frente-a-librerías)
11. [CLI: flags separados frente a formato único](#11-cli-flags-separados-frente-a-formato-único)
12. [LLM: Evaluación de APIs y modelos LLM](#12-llm-evaluación-de-apis-y-modelos-llm)
13. [LLM: SDK google-genai frente a alternativas](#13-llm-sdk-google-genai-frente-a-alternativas)
14. [LLM: Duck typing frente a clase base abstracta](#14-llm-duck-typing-frente-a-clase-base-abstracta)
15. [LLM: Manejo silencioso de errores de API](#15-llm-manejo-silencioso-de-errores-de-api)
16. [LLM: Configuración por variable de entorno frente a alternativas](#16-llm-configuración-por-variable-de-entorno-frente-a-alternativas)
17. [Detección de excepciones genéricas: AST frente a regex](#17-detección-de-excepciones-genéricas-ast-frente-a-regex)
18. [Detección de configuración hardcodeada: regex compiladas como constantes de clase](#18-detección-de-configuración-hardcodeada-regex-compiladas-como-constantes-de-clase)
19. [Detección de estado mutable compartido: dos fases complementarias](#19-detección-de-estado-mutable-compartido-dos-fases-complementarias)
20. [Ampliación de violaciones semánticas: prompts ampliados frente a prompts separados](#20-ampliación-de-violaciones-semánticas-prompts-ampliados-frente-a-prompts-separados)
21. [Heurísticas mock: búsqueda textual frente a visitor AST para detección de asserts](#21-heurísticas-mock-búsqueda-textual-frente-a-visitor-ast-para-detección-de-asserts)
22. [Clasificación a nivel de archivo frente a nivel de proyecto](#22-clasificación-a-nivel-de-archivo-frente-a-nivel-de-proyecto)
23. [Scoring ponderado para clasificación de archivos](#23-scoring-ponderado-para-clasificación-de-archivos)
24. [UI siempre gana en archivos mixtos](#24-ui-siempre-gana-en-archivos-mixtos)
25. [Auto-wait automático frente a solo configuración YAML](#25-auto-wait-automático-frente-a-solo-configuración-yaml)
26. [.gtaa.yaml frente a .env para configuración de reglas](#26-gtaayaml-frente-a-env-para-configuración-de-reglas)
27. [PyYAML con degradación elegante](#27-pyyaml-con-degradación-elegante)
28. [Parser Gherkin: regex frente a dependencia externa](#28-parser-gherkin-regex-frente-a-dependencia-externa)
29. [Herencia de keywords And/But para detección de Then](#29-herencia-de-keywords-andbut-para-detección-de-then)
30. [Detección de step definitions: path frente a AST](#30-detección-de-step-definitions-path-frente-a-ast)
31. [Detección de step patterns duplicados: check_project cross-file](#31-detección-de-step-patterns-duplicados-check_project-cross-file)
32. [Patrones de detalle de implementación en Gherkin](#32-patrones-de-detalle-de-implementación-en-gherkin)
33. [Multilenguaje: tree-sitter-language-pack frente a parsers separados](#33-multilenguaje-tree-sitter-language-pack-frente-a-parsers-separados)
34. [Checkers language-agnostic frente a checkers por lenguaje](#34-checkers-language-agnostic-frente-a-checkers-por-lenguaje)
35. [ParseResult como interfaz unificada frente a AST nativo](#35-parseresult-como-interfaz-unificada-frente-a-ast-nativo)
36. [Factory function frente a dispatcher manual para parsers](#36-factory-function-frente-a-dispatcher-manual-para-parsers)
37. [Python AST nativo frente a tree-sitter para Python](#37-python-ast-nativo-frente-a-tree-sitter-para-python)

---

## 1. Análisis de código: AST frente a alternativas

### Problema

El validador necesita analizar código Python para detectar violaciones arquitectónicas como:
- Funciones de test que llaman directamente a `driver.find_element()` en lugar de usar Page Objects
- Page Objects que contienen sentencias `assert` o lógica de negocio (`if/for/while`)
- Datos hardcodeados dentro de funciones de test

Se requiere un mecanismo de análisis que distinga el contexto sintáctico (dentro de qué función, clase o método se encuentra cada elemento) y que sea robusto ante variaciones de formato.

### Alternativa evaluada: Mapas anidados (diccionarios)

Un enfoque basado en diccionarios representaría el código como estructuras de datos manuales:

```python
code_map = {
    "functions": {
        "test_login": {
            "calls": ["driver.find_element", "login_page.login"],
            "strings": ["admin@test.com"],
            "lines": [10, 11, 12]
        }
    },
    "classes": {
        "LoginPage": {
            "methods": {
                "login": {
                    "has_assert": True,
                    "has_if": False
                }
            }
        }
    }
}
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Construcción manual | Requiere parsear el código de todas formas para llenar el diccionario, duplicando el trabajo que `ast.parse()` ya realiza |
| Estructura rígida | Cada nuevo tipo de violación exige modificar la estructura del mapa |
| Pérdida de contexto posicional | No se preserva el número de línea ni la jerarquía de anidamiento |
| Sin distinción de contexto | `driver.find_element()` a nivel de módulo y dentro de `test_login()` son situaciones distintas que un mapa plano no diferencia |

### Alternativa evaluada: Expresiones regulares (regex)

```python
import re
violations = re.findall(r'driver\.\w+\(', source_code)
```

**Motivos de descarte:**

| Problema | Ejemplo |
|----------|---------|
| Falsos positivos en comentarios | `# driver.find_element(...)` se detectaría como violación |
| Falsos positivos en cadenas | `"driver.find_element"` como dato de test |
| Sin contexto sintáctico | No distingue si el código está dentro de una función de test o una función auxiliar |
| Sin distinción de clases | No puede determinar si un `assert` está en un Page Object o en un test |
| Fragilidad ante formato | `driver . find_element()` o llamadas en múltiples líneas no se detectan |
| Mantenimiento costoso | Cada patrón nuevo es una regex que puede interferir con las existentes |

### Solución elegida: AST (Abstract Syntax Tree)

```python
tree = ast.parse(source_code)
visitor = BrowserAPICallVisitor()
visitor.visit(tree)
```

El módulo `ast` de la biblioteca estándar de Python genera un árbol sintáctico que representa la estructura completa del código fuente.

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Ignora comentarios y cadenas automáticamente | El parser solo genera nodos para código ejecutable |
| Contexto jerárquico nativo | Cada nodo conoce su posición en la jerarquía (módulo → clase → método → sentencia) |
| Información posicional | Cada nodo dispone de `lineno` y `col_offset` para reportar la ubicación exacta |
| Estándar de Python | `ast` pertenece a la biblioteca estándar, sin dependencias externas |
| Extensible | Añadir un nuevo visitor para detectar otro patrón no afecta a los existentes |
| Robusto | El AST es independiente del formato del código fuente |

### Ejemplo comparativo: detección de `assert` en Page Objects

```python
# Con regex (frágil):
if re.search(r'^\s+assert\s', line):
    # No se puede determinar si se está dentro de una clase o un método.

# Con AST (robusto):
class _AssertionVisitor(ast.NodeVisitor):
    def visit_ClassDef(self, node):
        self._in_class = True
        self.generic_visit(node)
        self._in_class = False

    def visit_FunctionDef(self, node):
        if self._in_class:
            self._in_method = True
            self.generic_visit(node)
            self._in_method = False

    def visit_Assert(self, node):
        if self._in_class and self._in_method:
            # Solo se reporta si el assert está dentro de un método de clase
            self.violations.append(...)
```

El AST proporciona la jerarquía `Clase → Método → Assert` de forma natural, sin necesidad de rastrear indentación.

### Uso complementario de regex

Las expresiones regulares se utilizan como **complemento** del AST en casos donde son la herramienta adecuada:

- **Detección de localizadores**: patrones como `By.ID, "login-btn"` dentro de cadenas ya extraídas por el AST
- **Datos hardcodeados**: emails, URLs, teléfonos — patrones dentro de nodos `ast.Constant` que el AST ya aisló
- **Nombres genéricos**: `test_1`, `test_a` — patrones sobre el nombre de la función

La combinación **AST para análisis estructural + regex para contenido de cadenas** proporciona la robustez necesaria.

---

## 2. Recorrido del AST: Patrón Visitor

### Problema

Una vez obtenido el AST, se necesita un mecanismo para recorrerlo y reaccionar ante tipos de nodo específicos manteniendo el contexto de anidamiento (por ejemplo, saber que una llamada a `driver.find_element()` está dentro de una función de test).

### Alternativa evaluada: `ast.walk()` con condicionales

```python
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
        for child in ast.walk(node):
            if isinstance(node, ast.Call):
                ...
```

**Motivos de descarte:**
- `ast.walk()` recorre en orden arbitrario, sin garantizar que el padre se procese antes que el hijo
- Se pierde el contexto de anidamiento al procesar nodos en bucles independientes
- El código se convierte en bucles anidados difíciles de mantener y extender

### Solución elegida: Patrón Visitor (`ast.NodeVisitor`)

```python
class BrowserAPICallVisitor(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        self._current_function = node.name
        self.generic_visit(node)       # Procesa hijos dentro del contexto
        self._current_function = None

    def visit_Call(self, node):
        if self._current_function:     # El contexto se mantiene durante el recorrido
            self._check_call(node)
        self.generic_visit(node)
```

El Patrón Visitor permite definir un método `visit_X()` para cada tipo de nodo AST. El recorrido en profundidad que realiza `generic_visit()` garantiza que el estado contextual (variables como `_in_class`, `_in_method`) se mantenga correctamente.

**Justificación:**
- **Recorrido en profundidad ordenado**: el padre siempre se visita antes que sus hijos
- **Estado contextual**: las variables de estado se mantienen correctamente durante todo el recorrido
- **Separación de responsabilidades**: cada método `visit_X` gestiona exactamente un tipo de nodo
- **Extensibilidad**: añadir detección de un nuevo tipo de nodo se reduce a implementar un método `visit_NuevoNodo()`
- **Integración con Python**: el módulo `ast` está diseñado para funcionar con este patrón

---

## 3. Organización de checkers: Patrón Strategy

### Problema

El validador necesita ejecutar diferentes tipos de verificaciones (llamadas a Selenium, aserciones en Page Objects, datos hardcodeados, estructura del proyecto). Se requiere una arquitectura que permita añadir nuevos tipos de verificación sin modificar el código existente.

### Descripción del patrón

El Patrón Strategy define una familia de algoritmos intercambiables detrás de una **interfaz común**. El cliente que los utiliza desconoce el algoritmo concreto y solo interactúa con la interfaz.

En este proyecto, la interfaz común es `BaseChecker`, que define tres métodos:

```
BaseChecker (interfaz abstracta)
    ├── can_check(file_path)    → Determina si el checker aplica a un archivo
    ├── check(file_path, tree)  → Analiza el archivo y devuelve violaciones
    └── check_project(path)     → Analiza el proyecto a nivel global

        ▲ implementan la misma interfaz
        │
    ┌───┴────────────────────────────────────┐
    │                                        │
DefinitionChecker  StructureChecker  AdaptationChecker  QualityChecker
```

Cada checker implementa los mismos métodos con lógica interna distinta:

| Checker | `can_check()` | `check()` |
|---------|---------------|-----------|
| DefinitionChecker | Archivos de test | Detecta llamadas a Selenium/Playwright |
| AdaptationChecker | Archivos de Page Object | Detecta asserts, imports prohibidos, lógica de negocio |
| QualityChecker | Archivos de test | Detecta datos hardcodeados, tests largos, nombres genéricos |
| StructureChecker | Siempre `False` | No opera a nivel de archivo (utiliza `check_project()`) |

### Justificación de la interfaz uniforme

Los métodos se denominan igual en todos los checkers porque el `StaticAnalyzer` los recorre en un bucle sin conocer la implementación concreta:

```python
# static_analyzer.py — el analizador es agnóstico respecto al checker concreto
for checker in self.checkers:
    if checker.can_check(file_path):
        violations = checker.check(file_path, tree)
```

Sin este patrón, el analizador necesitaría conocer cada checker individualmente:

```python
# Sin Strategy — acoplamiento directo con cada implementación
if isinstance(checker, DefinitionChecker):
    checker.check_selenium_calls(file_path)
elif isinstance(checker, AdaptationChecker):
    checker.check_page_object_violations(file_path)
elif isinstance(checker, QualityChecker):
    checker.check_test_quality(file_path)
# Cada checker nuevo exige modificar este código
```

Con el Patrón Strategy, incorporar un nuevo checker solo requiere:

1. Crear una clase que herede de `BaseChecker`
2. Añadirla a la lista en `_initialize_checkers()`

El `StaticAnalyzer` no se modifica, los tests existentes no se ven afectados y los demás checkers permanecen intactos.

### Alternativa evaluada: Clase monolítica

```python
class Analyzer:
    def check(self, file):
        # 500+ líneas con todas las verificaciones mezcladas
        self._check_selenium_calls(file)
        self._check_assertions(file)
        self._check_imports(file)
        self._check_structure(file)
        ...
```

**Motivos de descarte:**
- Un archivo de 500+ líneas resulta difícil de mantener y testear
- No es posible testear un tipo de verificación de forma aislada
- Añadir una verificación nueva requiere modificar la clase existente (viola el Principio Open/Closed)
- Los checkers no son reutilizables en otros contextos

### Resultado

| Ventaja | Descripción |
|---------|-------------|
| Tests unitarios aislados | Cada checker dispone de su propio conjunto de tests independiente |
| Open/Closed | Añadir checkers futuros implica crear archivos nuevos, sin modificar los existentes |
| Responsabilidad única | Cada checker gestiona exclusivamente su tipo de violación y sus archivos aplicables |
| Composición | El `StaticAnalyzer` compone checkers como piezas independientes |
| Desacoplamiento | El analizador desconoce los detalles internos de cada checker |

---

## 4. Orquestación: Patrón Facade

### Problema

El proceso de análisis involucra múltiples pasos: descubrimiento de archivos, parseo de AST, ejecución de checkers, cálculo de puntuación y generación del informe. Se necesita un punto de entrada simple que encapsule toda esta complejidad.

### Alternativa evaluada: invocación directa desde el CLI

```python
# El CLI gestionaría todos los pasos manualmente
checkers = [DefinitionChecker(), AdaptationChecker(), ...]
files = discover_files(path)
violations = []
for f in files:
    for c in checkers:
        if c.can_check(f):
            violations.extend(c.check(f))
# Calcular score, crear report...
```

### Solución elegida: `StaticAnalyzer` como Facade

```python
# El CLI únicamente conoce StaticAnalyzer
analyzer = StaticAnalyzer(path)
report = analyzer.analyze()
```

**Justificación:**
- El CLI no necesita conocer cuántos checkers existen ni cómo funcionan
- La lógica de descubrimiento de archivos, filtrado y scoring queda encapsulada
- Cuando se incorporen fases futuras (análisis con IA, etc.), el CLI no se modifica
- Proporciona un único punto de entrada para los tests de integración

---

## 5. Modelos de datos: Dataclasses y Enums

### Problema

Se necesitan estructuras de datos para representar violaciones e informes. Estas estructuras deben garantizar consistencia en los valores (tipos de violación, severidades) y facilitar la serialización a JSON.

### Alternativa evaluada: Diccionarios

```python
violation = {
    "type": "ADAPTATION_IN_DEFINITION",
    "severity": "CRITICAL",
    "line": 42,
    "message": "..."
}
# violation["typo"] → KeyError en tiempo de ejecución
# violation["severity"] → ¿"CRITICAL", "critical" o "Critical"?
```

### Solución elegida: Dataclasses + Enums

```python
@dataclass
class Violation:
    violation_type: ViolationType    # Solo valores válidos del Enum
    severity: Severity               # Auto-calculado desde violation_type
    file_path: Path
    line_number: Optional[int]
    message: str
```

**Justificación:**
- **Seguridad de tipos**: el IDE y los linters detectan errores antes de la ejecución
- **Auto-poblado**: `__post_init__` calcula `severity` y `recommendation` automáticamente a partir del `ViolationType`
- **Integridad**: la estructura es fija, no se pueden añadir campos arbitrarios
- **Serialización**: `to_dict()` en `Report` convierte todo a JSON de forma controlada

---

## 6. Verificación a dos niveles: proyecto y archivo

### Problema

`StructureChecker` necesita verificar la existencia de directorios como `tests/` y `pages/`. Esta es una propiedad del proyecto, no de ningún archivo individual, por lo que no encaja en el método `check()` que opera por archivo.

### Solución elegida: `check_project()` + `check()`

```python
class BaseChecker:
    def check(self, file_path) -> List[Violation]:            # Por archivo
        ...
    def check_project(self, project_path) -> List[Violation]: # Por proyecto
        return []  # Por defecto no realiza ninguna acción
```

- `check_project()` se ejecuta una vez antes del bucle de archivos
- `check()` se ejecuta por cada archivo que pasa el filtro `can_check()`
- `StructureChecker` solo implementa `check_project()`; su `can_check()` devuelve `False`
- Los otros tres checkers solo implementan `check()`

Esta separación evita forzar un paradigma único para dos necesidades distintas.

---

## 7. Optimización: parseo único del AST por archivo

### Problema

Cuando múltiples checkers analizan el mismo archivo, cada uno invocaba `ast.parse()` de forma independiente:

```python
# Antes: cada checker parsea por separado
class DefinitionChecker:
    def check(self, file_path):
        source = open(file_path).read()
        tree = ast.parse(source)          # Parse #1

class QualityChecker:
    def check(self, file_path):
        source = open(file_path).read()
        tree = ast.parse(source)          # Parse #2 (mismo archivo)
```

Un archivo de test es procesado por `DefinitionChecker` y `QualityChecker`, generando dos llamadas redundantes a `ast.parse()`.

### Solución elegida: parseo único en el analizador

```python
# El StaticAnalyzer parsea una vez y comparte el árbol
class StaticAnalyzer:
    def _check_file(self, file_path):
        tree = ast.parse(open(file_path).read())  # Parse único
        for checker in applicable:
            checker.check(file_path, tree)         # Reutiliza el árbol

class BaseChecker:
    def check(self, file_path, tree=None):         # tree es opcional
        if tree is None:
            tree = ast.parse(...)                   # Fallback para uso standalone
```

**Justificación:**
- **Elimina trabajo redundante**: con 4 checkers, un archivo se parseaba hasta 2-3 veces; ahora solo 1
- **Retrocompatible**: el parámetro `tree` es opcional, permitiendo usar los checkers de forma standalone
- **Responsabilidad clara**: el analizador gestiona I/O y parseo; los checkers solo analizan el árbol

**Caso especial — `AdaptationChecker`**: este checker necesita acceder al código fuente como texto para la detección de localizadores duplicados mediante regex. El archivo se lee dentro del checker, pero el AST no se vuelve a parsear.

**Decisión sobre el parámetro `source_code`**: se evaluó añadir `source_code` como parámetro adicional a `check()`, pero solo un checker (`AdaptationChecker`) lo necesita, y solo para una sub-verificación (localizadores duplicados). Añadir un parámetro que 3 de 4 checkers ignoran contaminaría la interfaz sin beneficio proporcional.

---

## 8. Paradigmas de programación utilizados

El proyecto se estructura en torno a dos paradigmas de programación.

### Programación Orientada a Objetos (paradigma principal)

Toda la arquitectura se fundamenta en Programación Orientada a Objetos. Este paradigma permite aplicar los patrones de diseño descritos en las secciones anteriores.

| Pilar de la POO | Aplicación en el proyecto | Ejemplo concreto |
|---|---|---|
| **Herencia** | `BaseChecker` como clase base de 4 checkers concretos | `class DefinitionChecker(BaseChecker)` |
| **Abstracción** | Interfaz abstracta con `@abstractmethod` | `BaseChecker.check()` define el contrato sin implementación |
| **Encapsulamiento** | Métodos y atributos privados con prefijo `_` | `_locator_registry`, `_check_forbidden_imports()`, `_in_class` |
| **Polimorfismo** | Cada checker implementa `check()` con lógica distinta | `StaticAnalyzer` invoca `checker.check()` sin conocer la clase concreta |

Los patrones de diseño aplicados (Strategy, Visitor, Facade) dependen directamente de la herencia y el polimorfismo proporcionados por la POO.

### Programación Declarativa (modelos de datos)

Para los modelos de datos se adopta un enfoque declarativo: se **describe la estructura** de los datos y Python genera automáticamente el comportamiento asociado.

```python
@dataclass
class Violation:
    violation_type: ViolationType    # Enum: restringe los valores válidos
    severity: Severity               # Enum: se auto-calcula en __post_init__
    file_path: Path
    line_number: Optional[int]
    message: str
```

| Herramienta declarativa | Aportación | Uso en el proyecto |
|---|---|---|
| `@dataclass` | Python genera `__init__`, `__repr__`, `__eq__` automáticamente | `Violation`, `Report` |
| `Enum` | Define un conjunto cerrado de valores válidos | `Severity`, `ViolationType` |
| `__post_init__` | Auto-rellena campos derivados a partir de otros | `Violation` calcula `severity` y `recommendation` desde `violation_type` |

### Justificación de la exclusión de programación funcional

El proyecto no utiliza programación funcional como paradigma de diseño. Existen usos puntuales de sintaxis funcional idiomática de Python (list comprehensions, `sum()` con generadores en `calculate_score()`), pero constituyen expresiones del lenguaje, no un paradigma arquitectónico.

La razón principal es que los patrones de diseño seleccionados (Strategy, Visitor) requieren estado mutable (`_in_class`, `_in_method`, `_locator_registry`) que se modifica durante el recorrido del AST. Un enfoque funcional puro obligaría a propagar este estado como parámetros entre llamadas sucesivas, incrementando la complejidad sin aportar beneficios para este tipo de proyecto.

---

## 9. Reportes: HTML autocontenido frente a alternativas

### Problema

El validador necesita generar un informe visual que permita a los usuarios revisar los resultados del análisis de forma cómoda. El informe debe ser portable (compartir por correo, abrir en cualquier ordenador) y no depender de conexión a internet.

### Alternativa evaluada: Jinja2 (template engine)

```python
from jinja2 import Template
template = Template(open("report_template.html").read())
html = template.render(report=report)
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Dependencia externa | Jinja2 no pertenece a la biblioteca estándar; añade una entrada a `requirements.txt` |
| Fichero de template separado | Requiere distribuir un fichero `.html` junto con el paquete Python |
| Sobredimensionado | Para un único template sin herencia ni bloques, Jinja2 no aporta ventajas frente a f-strings |

### Alternativa evaluada: Chart.js / Plotly (gráficos JavaScript)

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>new Chart(ctx, { type: 'bar', data: {...} });</script>
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Dependencia CDN | Requiere conexión a internet para cargar la librería JavaScript |
| No autocontenido | El fichero HTML no funciona offline sin incluir la librería completa (~200 KB) |
| Complejidad | Requiere generar JavaScript dinámico además de HTML |

### Alternativa evaluada: PDF con ReportLab / WeasyPrint

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Dependencias pesadas | WeasyPrint requiere Cairo y Pango (binarios del sistema operativo) |
| Instalación compleja | En Windows la instalación de estas dependencias es especialmente problemática |
| Sin interactividad | Un PDF no permite hover en filas de tabla ni reordenación |
| HTML → PDF gratuito | El navegador puede imprimir a PDF directamente (`Ctrl+P`) |

### Solución elegida: HTML autocontenido con f-strings y SVG inline

```python
class HtmlReporter:
    def generate(self, report, output_path):
        html_content = self._build_html(report)  # f-strings de Python
        output_path.write_text(html_content, encoding="utf-8")
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Cero dependencias | Solo usa módulos de la biblioteca estándar (`html`, `collections`, `pathlib`) |
| Autocontenido | Un solo fichero `.html` con CSS y SVG inline, sin assets externos |
| Portable | Funciona offline en cualquier navegador moderno |
| SVG nativo | Los gráficos (gauge, barras) se generan como SVG, escalables sin pérdida de calidad |
| Seguridad XSS | Todos los campos de usuario se escapan con `html.escape()` |
| Responsive | CSS con `grid`, `flex-wrap` y `@media` para adaptación a móvil |

### Decisión sobre XSS

El reporter escapa todos los campos que provienen del análisis (nombre de proyecto, rutas de fichero, mensajes de violación, snippets de código) mediante `html.escape()`. Esto previene inyección de HTML en caso de que un nombre de fichero o un snippet contenga caracteres como `<`, `>` o `"`.

---

## 10. Reportes: JSON con serialización propia frente a librerías

### Problema

El validador necesita exportar los resultados a un formato estructurado para integración programática (CI/CD, procesamiento automático).

### Alternativa evaluada: Pydantic / marshmallow

```python
class ReportSchema(BaseModel):
    metadata: MetadataSchema
    summary: SummarySchema
    violations: List[ViolationSchema]
```

**Motivos de descarte:**
- Añade una dependencia externa para un caso de uso simple
- El modelo `Report` ya dispone de `to_dict()` desde la Fase 2
- La serialización a JSON con `json.dumps()` es trivial y directa

### Solución elegida: `Report.to_dict()` + `json.dumps()`

```python
class JsonReporter:
    def generate(self, report, output_path):
        data = report.to_dict()
        output_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Reutiliza código existente | `to_dict()` ya convierte `Report` a diccionario serializable |
| `indent=2` | JSON legible para revisión humana directa |
| `ensure_ascii=False` | Preserva caracteres UTF-8 (español: `á`, `é`, `ñ`) sin escape Unicode |
| Sin dependencias | Solo usa `json` de la biblioteca estándar |

---

## 11. CLI: flags separados frente a formato único

### Problema

Se necesita una interfaz para que el usuario solicite la generación de reportes desde la línea de comandos. Existen dos enfoques posibles.

### Alternativa evaluada: `--format` con valor único

```bash
python -m gtaa_validator /path --format json --output report.json
python -m gtaa_validator /path --format html --output report.html
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Un solo formato por ejecución | No se pueden generar JSON y HTML simultáneamente |
| Dos flags obligatorios | Requiere `--format` y `--output` por separado |
| Más verboso | Más caracteres para el mismo resultado |

### Solución elegida: `--json PATH` y `--html PATH`

```bash
# Generar solo JSON
python -m gtaa_validator /path --json report.json

# Generar solo HTML
python -m gtaa_validator /path --html report.html

# Generar ambos simultáneamente
python -m gtaa_validator /path --json report.json --html report.html
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Generación simultánea | Ambos flags son compatibles entre sí |
| Un flag = formato + ruta | Cada flag indica el formato y la ruta de salida en un solo argumento |
| Compatible con salida de texto | La salida de texto del CLI se muestra siempre, independientemente de los flags |
| Conciso | Menos flags necesarios para el caso de uso más común |

---

## 12. LLM: Evaluación de APIs y modelos LLM

### Problema

El análisis semántico requiere un modelo LLM capaz de comprender código de test automation y detectar violaciones arquitectónicas. Se evaluaron diferentes proveedores y modelos, considerando capacidades de análisis de código, coste y disponibilidad.

### Modelos evaluados

| Modelo | Capacidad de código (SWE-Bench Verified) | Disponibilidad | Coste estimado |
|--------|------------------------------------------|----------------|----------------|
| Claude 4 Sonnet/Opus | 60-75% | De pago | Alto |
| Gemini 2.5 Pro | 63.8% | Free tier limitado | Gratuito (limitado) |
| GPT-4o | ~55% | De pago | Alto |
| DeepSeek V3 | ~45-50% | Muy barato | Bajo |
| Llama 3.3 70B | ~35-40% | Gratis (Groq) | Gratuito |
| **Gemini 2.5 Flash Lite** | **Suficiente para PoC** | **Free tier generoso** | **Gratuito** |

### APIs descartadas en esta fase

Todas las APIs de pago (Claude, GPT-4o, DeepSeek) se descartaron en esta fase por el coste de consumo. El proyecto realiza ~65 llamadas API por ejecución (6 de detección + ~59 de enriquecimiento), y sin una optimización previa de los prompts para reducir tokens y llamadas, el gasto sería difícil de justificar en un contexto de TFM.

| API descartada | Motivo principal |
|----------------|-----------------|
| OpenAI (GPT-4o) | Coste por token elevado; sin free tier viable para ~65 llamadas/ejecución |
| Anthropic (Claude) | Coste por token elevado; sin free tier |
| DeepSeek | Más barato, pero requiere pago y la latencia desde Europa es alta |
| Groq (Llama 3.3) | Gratuito pero menor capacidad de comprensión de código; free tier con límites de RPM |

### Solución elegida: Gemini 2.5 Flash Lite (free tier)

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Gratuito | 1000 requests/día y 15 RPM en el free tier |
| Capacidad suficiente | Detecta violaciones semánticas de forma competente para una PoC |
| SDK oficial | google-genai bien mantenido |
| Sin factura | Requisito del TFM: no generar costes innecesarios |

### Trabajo futuro: modelos locales y optimización

Para versiones futuras del proyecto se contemplan dos líneas de mejora, pendientes de exploración en profundidad:

1. **Optimización de prompts**: Reducir el número de tokens y llamadas API antes de considerar modelos de pago. Técnicas como batch de violaciones en una sola llamada o reducción del contexto enviado podrían reducir el consumo un 50-70%.

2. **Modelo local dockerizado**: Desplegar un modelo open-source (Llama, Mistral, CodeGemma) en un contenedor Docker, eliminando la dependencia de APIs externas y los límites de rate. Opciones como Ollama o vLLM permiten servir modelos localmente con una API compatible.

3. **Servidor dedicado**: Implementación directa en un servidor propio permitiendo modelos más grandes y sin restricciones de cuota.

Estas opciones se evaluarán cuando los prompts estén optimizados y se conozca el consumo real mínimo necesario para un análisis de calidad.

---

## 13. LLM: SDK google-genai frente a alternativas

### Problema

El análisis semántico requiere comunicarse con un modelo LLM. El modelo elegido es Gemini Flash de Google (gratuito y suficiente para el TFM). Se necesita decidir qué SDK usar para la comunicación.

### Alternativa evaluada: SDK openai (endpoint compatible)

```python
from openai import OpenAI
client = OpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=os.environ["GEMINI_API_KEY"])
response = client.chat.completions.create(model="gemini-2.0-flash", messages=[...])
```

Google ofrece un endpoint compatible con la API de OpenAI, lo que permite reusar el SDK `openai`.

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Dependencia engañosa | El código importa `openai` pero se comunica con Google, generando confusión |
| Funcionalidades limitadas | El endpoint compatible no soporta todas las features nativas de Gemini |
| Capa de compatibilidad | Se añade una traducción innecesaria de formatos (OpenAI → Gemini → OpenAI) |

### Alternativa evaluada: REST directo con requests

```python
import requests
response = requests.post(
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
    json={"contents": [{"parts": [{"text": prompt}]}]}
)
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Código boilerplate | Hay que construir manualmente los headers, body y parsear la respuesta |
| Sin tipado | No hay objetos de respuesta tipados, todo es `dict` |
| Sin reintentos | No hay retry automático ni manejo de rate limiting integrado |

### Solución elegida: google-genai (SDK nativo)

```python
from google import genai
client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=prompt,
    config=genai.types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.1,
    ),
)
text = response.text
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| SDK oficial | Mantenido por Google, sin capas de compatibilidad intermedias |
| API directa | `client.models.generate_content()` — una sola llamada |
| System instruction | Soporte nativo de `system_instruction` en la config |
| Tipado | Objetos de respuesta con atributos (`.text`, `.candidates`) |
| Coherencia | El import `from google import genai` refleja que se usa Google Gemini |

---

## 14. LLM: Duck typing frente a clase base abstracta

### Problema

El `SemanticAnalyzer` necesita aceptar tanto `MockLLMClient` como `GeminiLLMClient`. Ambos implementan los mismos métodos: `analyze_file()` y `enrich_violation()`.

### Alternativa evaluada: ABC (Abstract Base Class)

```python
from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    @abstractmethod
    def analyze_file(self, content: str, path: str) -> List[dict]: ...

    @abstractmethod
    def enrich_violation(self, violation: dict, content: str) -> str: ...

class MockLLMClient(BaseLLMClient): ...
class GeminiLLMClient(BaseLLMClient): ...
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Solo 2 implementaciones | Para dos clases con la misma interfaz, una ABC añade ceremonia sin beneficio proporcional |
| Modificación retroactiva | Requiere alterar `MockLLMClient` (ya existente y testeado) para heredar de la nueva ABC |
| Python idiomático | Duck typing es el enfoque natural en Python — "si camina como un pato..." |

### Solución elegida: Duck typing con Union type hint

```python
from typing import Union

class SemanticAnalyzer:
    def __init__(self, ..., llm_client: Union[MockLLMClient, GeminiLLMClient], ...):
        self.llm_client = llm_client
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Sin herencia | No requiere modificar las clases existentes |
| Type checking | El `Union` proporciona soporte a IDEs y type checkers |
| Extensible | Si se añade un tercer cliente, solo hay que actualizar el `Union` |
| Pragmático | Para un TFM con dos implementaciones, ABC sería sobreingeniería |

**Nota:** Si en el futuro se añaden más clientes (OpenAI, Claude, Ollama), se formalizaría con `BaseLLMClient(ABC)` y se actualizaría el type hint a la clase base.

---

## 15. LLM: Manejo silencioso de errores de API

### Problema

Las llamadas a la API de Gemini pueden fallar por múltiples razones (rate limiting, timeout, API key inválida, servidor caído). Se necesita decidir cómo manejar estos errores.

### Alternativa evaluada: Propagar excepciones

```python
def analyze_file(self, content, path):
    response = self.client.models.generate_content(...)  # Puede lanzar Exception
    return self._parse_violations(response.text)
    # Si falla, la excepción se propaga y aborta el análisis
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Rompe el flujo | Un error de API aborta todo el análisis, incluyendo el reporte estático ya completado |
| El análisis estático ya terminó | El `Report` con 35+ violaciones estáticas ya está listo; perderlo por un error de red es inaceptable |
| Rate limiting es frecuente | Con el free tier, los 429 son esperables; no deben ser fatales |

### Solución elegida: try/except silencioso con fallback vacío

```python
def analyze_file(self, content, path):
    try:
        response = self.client.models.generate_content(...)
        return self._parse_violations(response.text)
    except Exception:
        return []  # Silencioso: no rompe el flujo

def enrich_violation(self, violation, content):
    try:
        response = self.client.models.generate_content(...)
        return response.text.strip() or ""
    except Exception:
        return ""  # Silencioso: la violación queda sin sugerencia AI
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Resiliente | El análisis estático siempre se preserva, independientemente de fallos de la API |
| Degradación elegante | Sin API → sin violaciones semánticas ni sugerencias, pero el reporte sigue siendo útil |
| Consistente con mock | `MockLLMClient` nunca falla; `GeminiLLMClient` se comporta igual ante errores |
| Free tier friendly | Los 429 (rate limit) no abortan el análisis |

---

## 16. LLM: Configuración por variable de entorno frente a alternativas

### Problema

El `GeminiLLMClient` requiere una API key para autenticarse. Se necesita decidir cómo el usuario la proporciona.

### Alternativa evaluada: Flag del CLI

```bash
python -m gtaa_validator /path --ai --api-key AIzaSy...
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Seguridad | La API key queda en el historial de comandos del terminal |
| Verbosidad | Requiere copiar/pegar la key en cada ejecución |
| CI/CD | En pipelines automatizados, las variables de entorno son el estándar |

### Alternativa evaluada: Fichero de configuración

```yaml
# ~/.gtaa-validator/config.yml
gemini:
  api_key: AIzaSy...
  model: gemini-2.5-flash-lite
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Sobreingeniería | Para una sola variable, un fichero de configuración es excesivo |
| Ubicación no estándar | Requiere documentar dónde crear el fichero |
| Parsing | Requiere dependencia (pyyaml/toml) o implementar parsing propio |

### Solución elegida: Variable de entorno con .env

```bash
# .env (gitignored)
GEMINI_API_KEY=AIzaSy...

# __main__.py
from dotenv import load_dotenv
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY", "")
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Estándar de la industria | Variables de entorno es el mecanismo universal para secrets |
| Seguro | `.env` está en `.gitignore`; nunca se sube al repositorio |
| .env.example | Template para nuevos usuarios con instrucciones para obtener la key |
| python-dotenv | Librería ligera que carga `.env` automáticamente |
| CI/CD compatible | En pipelines, la variable se define directamente en el entorno |
| Fallback elegante | Sin key → `MockLLMClient` automático, sin error |

---

## 17. Detección de excepciones genéricas: AST frente a regex

### Problema

Se necesita detectar `except:` (bare) y `except Exception:` en archivos de test, ya que ocultan errores reales y dificultan el diagnóstico de fallos. Es necesario distinguir entre excepciones genéricas (violación) y específicas como `except ValueError:` (correcto).

### Alternativa evaluada: Regex sobre el código fuente

```python
import re
broad_except = re.findall(r'except\s*(?:Exception\s*)?:', source_code)
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Falsos positivos en strings | `"except Exception:"` dentro de una cadena se detectaría |
| Falsos positivos en comentarios | `# except:` se detectaría como violación |
| Dificultad con herencia | `except (TypeError, KeyError):` requiere regex complejas para parsear tuplas |

### Solución elegida: Inspección de `ast.ExceptHandler`

```python
for node in ast.walk(tree):
    if isinstance(node, ast.ExceptHandler):
        is_bare = node.type is None
        is_broad = isinstance(node.type, ast.Name) and node.type.id == "Exception"
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Preciso | `node.type is None` identifica exactamente `except:` sin ambigüedad |
| Ignora strings y comentarios | El AST solo contiene nodos ejecutables |
| Extensible | Se puede añadir detección de `BaseException` o excepciones custom |
| Línea exacta | `node.lineno` proporciona la ubicación precisa |

---

## 18. Detección de configuración hardcodeada: regex compiladas como constantes de clase

### Problema

Se necesita detectar URLs localhost, `time.sleep()` y paths absolutos embebidos en código de test. Estos valores deben externalizarse en configuración o fixtures.

### Alternativa evaluada: Análisis AST de strings

```python
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if "localhost" in node.value:
            ...
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| No cubre `time.sleep()` | `time.sleep(5)` es una llamada a función, no una string |
| Más verboso | Requiere detectar ast.Call para `time.sleep` + ast.Constant para URLs, duplicando lógica |
| Paths absolutos | Requiere AST + regex igualmente para validar patrones de path |

### Solución elegida: Regex compiladas como constantes de clase

```python
class QualityChecker:
    LOCALHOST_PATTERN = re.compile(r"https?://localhost[:\d/]|https?://127\.0\.0\.1[:\d/]")
    SLEEP_PATTERN = re.compile(r"time\.sleep\s*\(\s*\d")
    ABSOLUTE_PATH_PATTERN = re.compile(r'["\'][A-Z]:\\|["\']/home/|["\']/usr/|["\']/tmp/')
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Compilación única | Las regex se compilan una vez al cargar la clase, no por cada archivo |
| Cobertura uniforme | Un solo mecanismo detecta URLs, sleeps y paths sin mezclar AST y regex |
| Excluye comentarios | El check `stripped.startswith("#")` filtra comentarios antes de aplicar regex |
| Mantenible | Añadir un nuevo patrón (ej. `timeout=`) es una línea adicional |

---

## 19. Detección de estado mutable compartido: dos fases complementarias

### Problema

Los tests que comparten estado mutable a nivel de módulo (`shared_data = []`) o usan `global` dentro de funciones de test crean dependencias implícitas entre tests. Se necesita detectar ambos patrones.

### Alternativa evaluada: Detección única con `ast.walk()`

```python
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        # Problema: no distingue módulo-level de función-level
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| `ast.walk()` es plano | No distingue entre `shared = []` a nivel de módulo y `result = []` dentro de una función |
| Falsos positivos | Variables locales mutables dentro de tests serían flaggeadas incorrectamente |

### Solución elegida: Dos fases con `ast.iter_child_nodes()` + `ast.walk()`

**Fase 1** — `ast.iter_child_nodes(tree)` para variables de módulo:
- Solo inspecciona hijos directos del módulo (no desciende a funciones/clases)
- Verifica que el valor sea mutable: `ast.List`, `ast.Dict`, `ast.Set`, `ast.Call(list/dict/set)`
- Excluye MAYÚSCULAS (constantes) y `_prefijo` (privadas)

**Fase 2** — `ast.walk()` dentro de funciones `test_*` para `global`:
- Busca `ast.Global` solo dentro de funciones de test
- Reporta cada nombre declarado como global

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Sin falsos positivos | `iter_child_nodes` solo ve el primer nivel, evitando variables locales |
| Cobertura completa | Fase 1 cubre declaración mutable, Fase 2 cubre uso de `global` |
| Exclusiones razonables | MAYÚSCULAS y `_privadas` son patrones comunes que no indican estado compartido |

---

## 20. Ampliación de violaciones semánticas: prompts ampliados frente a prompts separados

### Problema

La Fase 6 añade 2 nuevos tipos de violación semántica (`MISSING_AAA_STRUCTURE`, `MIXED_ABSTRACTION_LEVEL`). Se necesita decidir cómo incorporarlos al análisis con LLM.

### Alternativa evaluada: Prompts separados por tipo

```python
# Un prompt especializado para cada tipo de violación
AAA_PROMPT = "Analiza si este test sigue el patrón AAA..."
ABSTRACTION_PROMPT = "Analiza si este método mezcla niveles de abstracción..."
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Más llamadas API | 2 prompts adicionales por archivo = +12 llamadas/ejecución |
| Rate limiting | Con el free tier (15 RPM), más llamadas incrementa el riesgo de 429 |
| Contexto duplicado | El mismo código fuente se envía múltiples veces |

### Solución elegida: Ampliar el prompt existente

Se añaden las 2 nuevas violaciones a la lista del `ANALYZE_FILE_PROMPT` existente, manteniendo una única llamada por archivo:

```
Busca SOLO estos tipos de violaciones:
- UNCLEAR_TEST_PURPOSE
- PAGE_OBJECT_DOES_TOO_MUCH
- IMPLICIT_TEST_DEPENDENCY
- MISSING_WAIT_STRATEGY
- MISSING_AAA_STRUCTURE          ← nuevo
- MIXED_ABSTRACTION_LEVEL        ← nuevo
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Misma cantidad de llamadas | 6 por ejecución (una por archivo), igual que en Fase 5 |
| Contexto compartido | El modelo ve todo el código y puede detectar múltiples tipos en una pasada |
| VALID_TYPES como filtro | El whitelist en `GeminiLLMClient` asegura que solo se aceptan tipos conocidos |

---

## 21. Heurísticas mock: búsqueda textual frente a visitor AST para detección de asserts

### Problema

El MockLLMClient necesita detectar si un test tiene aserciones para la heurística `MISSING_AAA_STRUCTURE`. Se necesita un mecanismo que identifique la presencia de `assert`, `assertEqual`, `assertTrue`, etc. en el cuerpo de una función de test.

### Alternativa evaluada: AST visitor para sentencias Assert

```python
class AssertFinder(ast.NodeVisitor):
    def __init__(self):
        self.found = False
    def visit_Assert(self, node):
        self.found = True
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Solo cubre `assert` nativo | `ast.Assert` detecta `assert x == y` pero no `self.assertEqual(x, y)` ni `mock.assert_called()` |
| Requiere visitor adicional | Para cubrir `assertEqual` habría que buscar `ast.Call` con nombres específicos |
| Más complejo | El visitor necesita rastrear múltiples tipos de nodo para un check simple |

### Solución elegida: Búsqueda textual en el código fuente del test

```python
assert_keywords = {"assert", "assertEqual", "assertTrue", "assertFalse",
                   "assertIn", "assertRaises", "assertIsNone", ...}
func_source = "\n".join(lines[node.lineno - 1:node.end_lineno])
has_assert = any(kw in func_source for kw in assert_keywords)
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Cobertura amplia | Detecta `assert`, `assertEqual`, `assert_called`, `assert_called_once` en una sola pasada |
| Simple | 3 líneas de código frente a un visitor completo |
| Heurística suficiente | Para el MockLLMClient (fallback), la precisión no necesita ser perfecta |
| Consistente | El GeminiLLMClient real complementa con análisis semántico más profundo |

**Nota:** Esta heurística tiene una limitación conocida: los nombres de función que contienen "assert" como subcadena (ej. `test_assert_helper`) pueden causar falsos negativos. En la práctica, esto es poco frecuente y el GeminiLLMClient real no tiene esta limitación.

---

## 22. Clasificación a nivel de archivo frente a nivel de proyecto

### Problema

La Fase 7 introduce soporte para proyectos mixtos que combinan tests de API y tests de UI. Violaciones como `ADAPTATION_IN_DEFINITION` y `MISSING_WAIT_STRATEGY` solo aplican a archivos de UI, pero no a archivos de API. Se necesita un mecanismo para determinar qué tipo de test contiene cada archivo.

### Alternativa evaluada: Clasificación a nivel de proyecto

```python
# Clasificar todo el proyecto como "api" o "ui"
project_type = classifier.classify_project(project_path)
if project_type == "api":
    skip_all_ui_checks()
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Pierde granularidad | Un proyecto con `tests/api/` y `tests/ui/` sería clasificado como uno solo |
| Falsos negativos | Si el proyecto es "api", los tests de UI no recibirían checks de UI |
| No refleja la realidad | Los proyectos reales mezclan ambos tipos de test |

### Solución elegida: Clasificación per-file

```python
class FileClassifier:
    def classify(self, file_path: Path, source: str, tree: ast.Module) -> str:
        """Clasifica cada archivo individualmente como 'api', 'ui' o 'unknown'."""
        api_score, ui_score = 0, 0
        # Analiza imports, código y path de ESTE archivo
        ...
        if api_score > 0 and ui_score == 0:
            return "api"
        elif ui_score > 0:
            return "ui"
        return "unknown"
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Granularidad máxima | Cada archivo se evalúa independientemente |
| Preciso | Un archivo con `import requests` es API aunque el proyecto tenga Selenium |
| Sin configuración | Funciona automáticamente sin necesidad de `.gtaa.yaml` |
| Conservador | `unknown` se trata como UI (no pierde violaciones) |

---

## 23. Scoring ponderado para clasificación de archivos

### Problema

La clasificación de archivos necesita combinar múltiples señales: imports del AST, patrones de código (regex) y patrones de path. Se requiere un mecanismo que pondere estas señales según su fiabilidad.

### Alternativa evaluada: Reglas binarias (if/elif)

```python
# Si tiene import requests → API
if has_api_import:
    return "api"
# Si tiene import selenium → UI
elif has_ui_import:
    return "ui"
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| No combina señales | Un archivo con `response.status_code` pero sin imports API no se clasifica |
| Reglas frágiles | Requiere encadenar condiciones OR/AND para cubrir combinaciones |
| Difícil de extender | Cada nueva señal requiere reestructurar los condicionales |

### Solución elegida: Scoring con pesos diferenciados

```python
# Pesos por tipo de señal (mayor = más fiable)
# Imports AST:  +5 (más fiable, semántico)
# Código regex: +2 (menos fiable, puede estar en strings)
# Path:         +3 (fiable, convención de equipo)

for node in ast.walk(tree):
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        if module_name in self.API_IMPORTS:
            api_score += 5
        elif module_name in self.UI_IMPORTS:
            ui_score += 5

for pattern in self.API_CODE_PATTERNS:
    if re.search(pattern, source):
        api_score += 2
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Combina señales débiles | `response.status_code` (2) + `/api/` en path (3) = API score 5 |
| Pesos semánticos | Imports (AST) pesan más que regex porque son más fiables |
| Extensible | Añadir nueva señal = añadir al set y asignar peso |
| Umbral simple | `api_score > 0 and ui_score == 0` es claro y fácil de razonar |

---

## 24. UI siempre gana en archivos mixtos

### Problema

Algunos archivos pueden tener señales de API y UI simultáneamente (ej. un test de UI que hace una llamada HTTP para setup). Cuando ambos scores son positivos, se necesita una regla de desempate.

### Alternativa evaluada: Usar el score mayor

```python
if api_score > ui_score:
    return "api"
elif ui_score > api_score:
    return "ui"
else:
    return "unknown"
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Riesgo de falsos negativos | Si un test de UI tiene `import requests` para setup, podría clasificarse como API |
| Pierde violaciones | Un archivo API no recibe `ADAPTATION_IN_DEFINITION` ni `MISSING_WAIT_STRATEGY` |
| Menos seguro | Los falsos negativos son peores que los falsos positivos en un validador |

### Solución elegida: UI siempre gana (regla conservadora)

```python
if api_score > 0 and ui_score == 0:
    return "api"    # Solo API si NO hay señales UI
elif ui_score > 0:
    return "ui"     # UI siempre gana si hay cualquier señal UI
return "unknown"    # Sin señales → tratado como UI
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Sin falsos negativos | Si hay cualquier señal UI, se aplican todos los checks |
| Principio de precaución | Mejor reportar una violación extra que perder una real |
| Simple de razonar | La regla es: "solo es API si NO tiene nada de UI" |
| Alineado con el propósito | Un validador debe detectar problemas, no ocultarlos |

---

## 25. Auto-wait automático frente a solo configuración YAML

### Problema

Playwright tiene auto-wait integrado en todas sus acciones (click, fill, etc.), lo que hace que `MISSING_WAIT_STRATEGY` sea un falso positivo para proyectos Playwright. Se necesita un mecanismo para detectar esto y suprimir la violación.

### Alternativa evaluada: Solo configuración YAML

```yaml
# .gtaa.yaml
exclude_checks:
  - MISSING_WAIT_STRATEGY  # Manual: el usuario debe saber configurarlo
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Fricción innecesaria | Playwright siempre tiene auto-wait — no es una decisión del equipo |
| Olvido del usuario | Un proyecto Playwright sin `.gtaa.yaml` recibiría falsos positivos |
| Acoplado a conocimiento | El usuario necesita saber que Playwright tiene auto-wait |

### Solución elegida: Detección automática + YAML para casos custom

```python
# ClassificationResult.has_auto_wait detecta automáticamente
AUTO_WAIT_FRAMEWORKS = {"playwright"}

@property
def has_auto_wait(self) -> bool:
    return bool(self.detected_frameworks & self.AUTO_WAIT_FRAMEWORKS)

# YAML complementa para frameworks custom no detectables
# .gtaa.yaml: frameworks_auto_wait: ["cypress-python"]
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Zero config para Playwright | Funciona sin `.gtaa.yaml` si hay `from playwright...` |
| YAML como complemento | Frameworks custom pueden declarar auto-wait manualmente |
| Basado en hechos | Playwright tiene auto-wait por diseño — es detectable sin configuración |
| Extensible | Nuevos frameworks se añaden al set `AUTO_WAIT_FRAMEWORKS` |

---

## 26. .gtaa.yaml frente a .env para configuración de reglas

### Problema

La Fase 7 necesita un mecanismo para que los equipos configuren exclusiones de reglas (`exclude_checks`), paths ignorados (`ignore_paths`) y patrones custom de archivos API. Se necesita decidir dónde almacenar esta configuración.

### Alternativa evaluada: Reutilizar `.env`

```bash
# .env
GEMINI_API_KEY=sk-xxx
GTAA_EXCLUDE_CHECKS=MISSING_WAIT_STRATEGY,POOR_TEST_NAMING
GTAA_IGNORE_PATHS=tests/legacy/**
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Semántica incorrecta | `.env` es para secretos (API keys), no para configuración de equipo |
| No se commitea | `.env` está en `.gitignore` — las exclusiones no se comparten |
| Formato plano | Variables de entorno no soportan listas/objetos bien |

### Alternativa evaluada: `pyproject.toml` con sección `[tool.gtaa]`

```toml
[tool.gtaa]
exclude_checks = ["MISSING_WAIT_STRATEGY"]
ignore_paths = ["tests/legacy/**"]
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Acoplado a Python | `pyproject.toml` es específico del ecosistema Python |
| Archivo compartido | Mezcla configuración de build con configuración del validador |

### Solución elegida: Archivo `.gtaa.yaml` dedicado

```yaml
# .gtaa.yaml — configuración de equipo (se commitea)
exclude_checks:
  - MISSING_WAIT_STRATEGY    # Ej: Playwright auto-waits
ignore_paths:
  - "tests/legacy/**"
api_test_patterns:
  - "**/test_api_*.py"
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Semántico | El nombre `.gtaa.yaml` indica claramente su propósito |
| Commitable | Configuración de equipo que debe versionarse |
| YAML legible | Soporta listas y objetos de forma natural |
| Autocontenido | No mezcla con configuración de build ni secretos |
| Agnóstico | No depende del ecosistema Python — útil si se porta a otro lenguaje |

---

## 27. PyYAML con degradación elegante

### Problema

El módulo `config.py` necesita parsear archivos `.gtaa.yaml`. Se requiere una dependencia de YAML y una estrategia para manejar errores (archivo inexistente, YAML inválido, campos faltantes).

### Alternativa evaluada: Fallo estricto (raise en error)

```python
def load_config(project_path: Path) -> ProjectConfig:
    config_path = project_path / ".gtaa.yaml"
    with open(config_path) as f:
        data = yaml.safe_load(f)  # Raises si no existe o es inválido
    return ProjectConfig(**data)   # Raises si faltan campos
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Bloquea análisis | Un YAML con error de sintaxis impide usar el validador |
| Obligatorio | Requiere que `.gtaa.yaml` exista en todos los proyectos |
| Frágil | Un campo faltante o tipo incorrecto causa crash |

### Solución elegida: Degradación elegante con defaults vacíos

```python
def load_config(project_path: Path, config_path: Optional[Path] = None) -> ProjectConfig:
    path = config_path or project_path / ".gtaa.yaml"
    if not path.exists():
        return ProjectConfig()  # Defaults vacíos
    try:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return ProjectConfig(
            exclude_checks=data.get("exclude_checks", []),
            ignore_paths=data.get("ignore_paths", []),
            api_test_patterns=data.get("api_test_patterns", []),
        )
    except Exception:
        return ProjectConfig()  # YAML inválido → defaults
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Zero config | El validador funciona sin `.gtaa.yaml` |
| Robusto | YAML inválido no bloquea el análisis |
| Parcial | Un YAML con solo `exclude_checks` funciona — los demás campos usan defaults |
| Consistente | Mismo patrón que el manejo de errores LLM (ADR 15: degradación elegante) |

---

## 28. Parser Gherkin: regex frente a dependencia externa

### Problema

La Fase 8 añade soporte para archivos `.feature` (Gherkin) en proyectos BDD (Behave, pytest-bdd). Se necesita un parser que extraiga Features, Scenarios, Background y Steps con sus keywords (Given/When/Then/And/But).

### Alternativa evaluada: gherkin-official (dependencia externa)

```python
from gherkin.parser import Parser
parser = Parser()
gherkin_document = parser.parse(feature_content)
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Dependencia adicional | Añade `gherkin-official` a requirements.txt |
| Complejidad del output | Genera un AST complejo con pickles, backgrounds, etc. |
| Overengineering | Solo necesitamos líneas de steps para regex, no un AST completo |

### Solución elegida: Parser regex propio

```python
class GherkinParser:
    FEATURE_RE = re.compile(r'^\s*Feature:\s*(.+)', re.IGNORECASE)
    SCENARIO_RE = re.compile(r'^\s*Scenario:\s*(.+)', re.IGNORECASE)
    STEP_RE = re.compile(r'^\s*(Given|When|Then|And|But)\s+(.+)', re.IGNORECASE)

    def parse(self, content: str) -> Optional[GherkinFeature]:
        # Línea por línea, regex simples
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Sin dependencias | Gherkin tiene sintaxis muy regular — regex son suficientes |
| Ligero | ~180 líneas de código vs una dependencia externa |
| Control total | Extraemos exactamente lo que necesitamos (keyword, text, line) |
| Testeable | Fácil de mockear y testear sin dependencias externas |
| Seguridad | Minimizar dependencias externas reduce la superficie de ataque y el riesgo de vulnerabilidades en librerías de terceros (supply chain security) |

---

## 29. Herencia de keywords And/But para detección de Then

### Problema

En Gherkin, `And` y `But` heredan el keyword del step anterior. Un scenario como:

```gherkin
Given I am logged in
And I have items in cart     # ← This is effectively a "Given"
When I checkout
Then I see confirmation
And I receive email          # ← This is effectively a "Then"
```

La propiedad `has_then` debe detectar correctamente si el scenario tiene verificación, incluso cuando el `Then` está seguido de `And`.

### Alternativa evaluada: Buscar keyword literal "Then"

```python
def has_then(self):
    return any(step.keyword == "Then" for step in self.steps)
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Pierde And/But | Un scenario con `Then X` + `And Y` + `And Z` solo contaría el primer Then |
| Falsos negativos | Un scenario con `Given`, `When`, `Then`, `And` sería marcado incorrectamente |

### Solución elegida: Rastreo de keyword efectivo

```python
def _has_effective_keyword(self, keyword: str) -> bool:
    effective = None
    for step in self.steps:
        if step.keyword in ("Given", "When", "Then"):
            effective = step.keyword
        # And/But heredan el keyword del step anterior
        if effective == keyword:
            return True
    return False
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Semántica correcta | `And` después de `Then` cuenta como `Then` |
| Detección precisa | `has_then` es True si hay al menos un step con keyword efectivo Then |
| Estándar Gherkin | Sigue la semántica oficial de Gherkin |

---

## 30. Detección de step definitions: path frente a AST

### Problema

El BDDChecker necesita identificar qué archivos Python son step definitions (contienen `@given`, `@when`, `@then`) para aplicar las reglas BDD. Se necesita un mecanismo de detección.

### Alternativa evaluada: Solo inspección AST de decoradores

```python
def is_step_definition(file_path: Path, tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if decorator.func.id in ("given", "when", "then"):
                    return True
    return False
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Requiere parsear AST | Hay que leer y parsear cada archivo para determinar si es step def |
| Costoso | En `can_check()` esto se ejecuta para TODOS los archivos |
| No disponible | `can_check()` recibe solo el path, no el AST |

### Solución elegida: Detección por path + validación AST posterior

```python
def _is_step_definition_path(self, file_path: Path) -> bool:
    parts = [p.lower() for p in file_path.parts]
    name = file_path.name.lower()
    return (
        "steps" in parts
        or "step_defs" in parts
        or "step_definitions" in parts
        or name.endswith("_steps.py")
    )

def _is_step_function(self, node: ast.FunctionDef) -> bool:
    # Validación AST solo para funciones dentro de archivos candidatos
    step_decorators = {"given", "when", "then", "step"}
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call):
            if decorator.func.id.lower() in step_decorators:
                return True
    return False
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Filtrado rápido | `can_check()` usa solo el path — O(1) |
| Convención estándar | Behave y pytest-bdd usan `steps/` por convención |
| Validación precisa | Las funciones individuales se validan por AST en `check()` |
| Dos niveles | Path filtra archivos, AST filtra funciones dentro de ellos |

---

## 31. Detección de step patterns duplicados: check_project cross-file

### Problema

En proyectos BDD, dos archivos de step definitions pueden definir el mismo pattern (ej. `@given("I am on the login page")`), causando conflictos en runtime. Se necesita detectar duplicados entre archivos.

### Alternativa evaluada: Detección en `check()` por archivo

```python
def check(self, file_path, tree, ...):
    patterns = self._extract_patterns(tree)
    for pattern in patterns:
        if pattern in self._global_patterns:
            # Violación
        self._global_patterns.add(pattern)
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Orden-dependiente | El primer archivo no detecta el duplicado — solo el segundo |
| Estado persistente | `_global_patterns` acumula entre ejecuciones si no se resetea |
| No idempotente | Ejecutar dos veces da resultados diferentes |

### Solución elegida: check_project con recolección previa

```python
def check_project(self, project_path: Path) -> List[Violation]:
    self._step_patterns = {}  # Reset en cada ejecución

    # Fase 1: Recolectar todos los patterns
    for py_file in project_path.rglob("*.py"):
        if self._is_step_definition_path(py_file):
            self._collect_step_patterns(py_file)

    # Fase 2: Detectar duplicados
    for pattern, files in self._step_patterns.items():
        if len(files) > 1:
            for dup_file in files[1:]:
                violations.append(Violation(
                    type=DUPLICATE_STEP_PATTERN,
                    file_path=dup_file,
                    message=f"Pattern duplicado. También en: {files[0]}"
                ))
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Idempotente | Reset del dict en cada ejecución |
| Vista global | Conoce todos los patterns antes de reportar |
| Reporte en archivo correcto | El "segundo" archivo (duplicado) recibe la violación |
| Contexto útil | El mensaje indica dónde está el original |

---

## 32. Patrones de detalle de implementación en Gherkin

### Problema

Los archivos `.feature` deben usar lenguaje de negocio, no detalles técnicos. Se necesita detectar XPath, CSS selectors, URLs, SQL y otros detalles de implementación en los steps.

### Alternativa evaluada: Lista de palabras prohibidas

```python
FORBIDDEN_WORDS = ["xpath", "css", "selector", "localhost", "http"]
for word in FORBIDDEN_WORDS:
    if word in step.text.lower():
        # Violación
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Falsos positivos | "I search for CSS tutorial" contendría "css" |
| Falsos negativos | `//input[@id='user']` no contiene ninguna palabra prohibida explícita |
| No distingue contexto | "localhost" en un step sobre configuración local es legítimo |

### Solución elegida: Regex específicas por tipo

```python
IMPLEMENTATION_PATTERNS = [
    re.compile(r'//[\w\[\]@=\'"\.]+'),           # XPath
    re.compile(r'css='),                          # CSS prefix
    re.compile(r'#[\w-]{3,}'),                    # CSS ID (#username)
    re.compile(r'\.[\w-]{3,}\b'),                 # CSS class (.btn-primary)
    re.compile(r'By\.\w+'),                       # Selenium By.*
    re.compile(r'\[data-[\w-]+'),                 # data attributes
    re.compile(r'https?://\S+'),                  # URLs
    re.compile(r'SELECT\s+.+\s+FROM', re.I),     # SQL SELECT
    re.compile(r'INSERT\s+INTO', re.I),          # SQL INSERT
    re.compile(r'localhost:\d+'),                 # localhost URLs
    re.compile(r'<[\w/]+>'),                      # HTML tags
]
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Precisión | `//input[@id]` detecta XPath real, no "xpath" como palabra |
| Mínimos falsos positivos | Los patterns son específicos (ej. `#` requiere 3+ chars) |
| Extensible | Añadir nuevo patrón es una línea |
| Cobertura amplia | XPath, CSS, SQL, URLs, HTML — todos los técnicos comunes |

---

## 33. Multilenguaje: tree-sitter-language-pack frente a parsers separados

### Problema

La Fase 9 añade soporte para proyectos de test automation en Java, JavaScript/TypeScript y C#. Se necesita un mecanismo de parsing que funcione para múltiples lenguajes sin añadir una dependencia por cada lenguaje.

### Alternativa evaluada: Parsers separados por lenguaje

```python
# Dependencias separadas
import javalang        # Java
import esprima         # JavaScript
import tree_sitter     # TypeScript (requiere bindings)
import csharp_parser   # C# (hipotético)
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Múltiples dependencias | Cada lenguaje requiere una librería diferente con API distinta |
| Mantenimiento fragmentado | Cada parser tiene ciclo de releases independiente |
| APIs inconsistentes | `javalang` devuelve objetos Java-like, `esprima` devuelve JSON, etc. |
| Sin TypeScript nativo | `esprima` no soporta TypeScript; requiere transpilación previa |

### Alternativa evaluada: Parser genérico (pygments/tokenizers)

```python
import pygments
tokens = pygments.lex(source, JavaLexer())
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Solo tokenización | Pygments genera tokens, no un AST con jerarquía |
| Sin contexto sintáctico | No distingue si un token está dentro de una función o clase |
| No detecta estructuras | No puede extraer métodos, decoradores ni herencias |

### Solución elegida: tree-sitter-language-pack

```python
from tree_sitter_language_pack import get_parser
parser = get_parser("java")       # Java
parser = get_parser("javascript") # JavaScript
parser = get_parser("typescript") # TypeScript
# C# usa paquete separado: tree-sitter-c-sharp
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Una dependencia | `tree-sitter-language-pack` incluye 165+ lenguajes en un solo paquete |
| API unificada | `parser.parse(source)` funciona igual para todos los lenguajes |
| Pre-built wheels | No requiere compilar bindings; instalación trivial con `pip install` |
| TypeScript nativo | Soporta TypeScript sin transpilación |
| AST completo | Genera árbol sintáctico navegable con tipos de nodo consistentes |
| Licencia permisiva | MIT/Apache 2.0, compatible con uso comercial y académico |

**Caso especial — C#:**

C# no está incluido en `tree-sitter-language-pack` y requiere el paquete separado `tree-sitter-c-sharp`. La API es idéntica, solo cambia el import:

```python
import tree_sitter_c_sharp as tscs
from tree_sitter import Parser, Language
parser = Parser(Language(tscs.language()))
```

**Requisito Python ≥ 3.10:**

`tree-sitter-language-pack` requiere Python 3.10+ debido a dependencias internas de `tree-sitter` 0.25.x. El proyecto actualiza `python_requires` en `setup.py` de 3.8 a 3.10.

---

## 34. Checkers language-agnostic frente a checkers por lenguaje

### Problema

Con soporte para 4 lenguajes (Python, Java, JS/TS, C#), surge la pregunta: ¿crear checkers separados por lenguaje o hacer los checkers existentes language-agnostic?

### Alternativa evaluada: Un checker por lenguaje

```
gtaa_validator/checkers/
├── definition_checker.py      # Python
├── adaptation_checker.py      # Python
├── quality_checker.py         # Python
├── java_checker.py            # Java (NUEVO)
├── js_checker.py              # JavaScript/TypeScript (NUEVO)
├── csharp_checker.py          # C# (NUEVO)
```

```python
class JavaChecker(BaseChecker):
    def can_check(self, file_path):
        return file_path.suffix == ".java"

    def check(self, file_path, tree, file_type):
        # Reimplementar TODA la lógica de violaciones para Java:
        # - ADAPTATION_IN_DEFINITION
        # - HARDCODED_TEST_DATA
        # - ASSERTION_IN_POM
        # - POOR_TEST_NAMING
        # - LONG_TEST_FUNCTION
        # - etc.
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Duplicación masiva | Cada checker reimplementa la misma lógica (email regex, naming patterns, etc.) |
| Mantenimiento × 4 | Añadir una violación nueva requiere modificar 4 archivos |
| Inconsistencias | Fácil que Java detecte `HARDCODED_TEST_DATA` con una regex y C# con otra |
| Pruebas × 4 | Cada checker necesita su propio conjunto de tests casi idénticos |
| Viola DRY | "Don't Repeat Yourself" — el código de detección es el mismo, solo cambia el AST |

### Solución elegida: Checkers language-agnostic con ParseResult unificado

```
gtaa_validator/checkers/
├── definition_checker.py      # Todos los lenguajes
├── adaptation_checker.py      # Todos los lenguajes
├── quality_checker.py         # Todos los lenguajes
├── structure_checker.py       # Proyecto (sin cambios)
├── bdd_checker.py             # Gherkin (sin cambios)
```

```python
class DefinitionChecker(BaseChecker):
    # Métodos browser por lenguaje
    BROWSER_METHODS_PYTHON = {"find_element", "find_elements", "get", ...}
    BROWSER_METHODS_JAVA = {"findElement", "findElements", "get", ...}
    BROWSER_METHODS_JS = {"locator", "getByRole", "getByText", "$", ...}
    BROWSER_METHODS_CSHARP = {"FindElement", "FindElements", "Navigate", ...}

    def _get_browser_methods(self, extension: str) -> Set[str]:
        """Retorna los métodos browser según la extensión del archivo."""
        if extension == ".py":
            return self.BROWSER_METHODS_PYTHON
        elif extension == ".java":
            return self.BROWSER_METHODS_JAVA
        elif extension in {".js", ".ts", ".jsx", ".tsx"}:
            return self.BROWSER_METHODS_JS
        elif extension == ".cs":
            return self.BROWSER_METHODS_CSHARP
        return set()

    def check(self, file_path, result: ParseResult, file_type):
        extension = file_path.suffix.lower()
        browser_methods = self._get_browser_methods(extension)
        # Lógica ÚNICA que funciona con cualquier ParseResult
        for call in result.calls:
            if call.method_name in browser_methods:
                # Crear violación...
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| DRY cumplido | La lógica de detección está en UN lugar; solo los patrones varían |
| Mantenimiento centralizado | Añadir violación = modificar 1 archivo, no 4 |
| Consistencia garantizada | Todos los lenguajes usan el mismo algoritmo |
| Tests compartidos | Un test parametrizado cubre todos los lenguajes |
| Open/Closed | Añadir lenguaje = añadir entrada a los dicts, no reescribir clases |

**Arquitectura resultante:**

```
                    ParseResult (interfaz unificada)
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    PythonParser      JavaParser      JSParser      CSharpParser
    (ast nativo)     (tree-sitter)  (tree-sitter)  (tree-sitter)
           │               │               │               │
           └───────────────┴───────────────┴───────────────┘
                           │
                           ▼
              ┌────────────────────────────┐
              │   Checkers Language-Agnostic   │
              │   (DefinitionChecker, etc.)    │
              │   Reciben ParseResult          │
              │   Usan dicts por extensión     │
              └────────────────────────────┘
```

Esta arquitectura sigue el **Principio de Inversión de Dependencias**: los checkers de alto nivel dependen de la abstracción `ParseResult`, no de los parsers concretos.

### Refactor realizado

Los checkers `DefinitionChecker`, `AdaptationChecker` y `QualityChecker` existían desde la Fase 2 y funcionaban exclusivamente con Python AST. El refactor de Fase 9 los transformó en checkers language-agnostic:

**ANTES (Fase 2-8) — Solo Python:**

```python
class DefinitionChecker(BaseChecker):
    """Checker acoplado a ast.Module de Python."""

    BROWSER_METHODS = {"find_element", "find_elements", "get", ...}

    def can_check(self, file_path: Path) -> bool:
        return file_path.suffix == ".py"

    def check(self, file_path: Path, tree: ast.Module, file_type: str):
        # Recorre ast.Module directamente
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in self.BROWSER_METHODS:
                        # Crear violación...
```

**DESPUÉS (Fase 9) — Todos los lenguajes:**

```python
class DefinitionChecker(BaseChecker):
    """Checker desacoplado que trabaja con ParseResult."""

    # Patrones por lenguaje
    BROWSER_METHODS_PYTHON = {"find_element", "find_elements", "get", ...}
    BROWSER_METHODS_JAVA = {"findElement", "findElements", "get", ...}
    BROWSER_METHODS_JS = {"locator", "getByRole", "$", ...}
    BROWSER_METHODS_CSHARP = {"FindElement", "FindElements", ...}

    def can_check(self, file_path: Path) -> bool:
        # Ahora acepta múltiples extensiones
        return file_path.suffix.lower() in {
            ".py", ".java", ".js", ".ts", ".tsx", ".jsx", ".cs"
        }

    def check(self, file_path: Path, result: ParseResult, file_type: str):
        extension = file_path.suffix.lower()
        browser_methods = self._get_browser_methods(extension)

        # Trabaja con ParseResult abstracto, no con AST concreto
        for call in result.calls:
            if call.method_name in browser_methods:
                # Crear violación...
```

**Cambios clave del refactor:**

| Aspecto | Antes | Después |
|---------|-------|---------|
| Parámetro de entrada | `tree: ast.Module` | `result: ParseResult` |
| Extensiones soportadas | Solo `.py` | `.py`, `.java`, `.js`, `.ts`, `.cs`, etc. |
| Patrones de detección | `BROWSER_METHODS` (único) | `BROWSER_METHODS_*` (por lenguaje) |
| Recorrido de código | `ast.walk(tree)` | `for call in result.calls` |
| Acoplamiento | Alto (a `ast` module) | Bajo (a `ParseResult` abstracción) |

---

## 35. ParseResult como interfaz unificada frente a AST nativo

### Problema

Cada lenguaje tiene su propia representación de AST:
- Python: `ast.Module` con nodos `ast.FunctionDef`, `ast.Call`, etc.
- Java (tree-sitter): nodos `class_declaration`, `method_invocation`, etc.
- JS/TS (tree-sitter): nodos `function_declaration`, `call_expression`, etc.

Los checkers necesitan una forma uniforme de acceder a funciones, clases, llamadas e imports sin conocer el lenguaje.

### Alternativa evaluada: Pasar AST nativo + helper functions

```python
def check(self, file_path, tree, file_type):
    if isinstance(tree, ast.Module):
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    elif is_java_tree(tree):
        functions = extract_java_methods(tree)
    elif is_js_tree(tree):
        functions = extract_js_functions(tree)
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Lógica condicional en checkers | Cada checker necesita switch por tipo de AST |
| Helpers dispersos | Las funciones de extracción estarían en módulos separados |
| Tipos inconsistentes | `ast.FunctionDef` vs `tree_sitter.Node` tienen APIs diferentes |
| Duplicación de extracción | Si 3 checkers necesitan funciones, cada uno extrae |

### Solución elegida: ParseResult como estructura de datos común

```python
@dataclass
class ParsedFunction:
    name: str
    line_start: int
    line_end: int
    decorators: List[str]
    parameters: List[str]
    is_async: bool

@dataclass
class ParsedCall:
    object_name: str   # driver, page, cy
    method_name: str   # findElement, locator, get
    line: int
    full_text: str

@dataclass
class ParseResult:
    imports: List[ParsedImport]
    classes: List[ParsedClass]
    functions: List[ParsedFunction]
    calls: List[ParsedCall]
    strings: List[ParsedString]
    language: str
    parse_errors: List[str]
```

Cada parser (PythonParser, JavaParser, JSParser, CSharpParser) produce un `ParseResult` con la misma estructura:

```python
class PythonParser:
    def parse(self, source: str) -> ParseResult:
        tree = ast.parse(source)
        return ParseResult(
            imports=self._extract_imports(tree),
            classes=self._extract_classes(tree),
            functions=self._extract_functions(tree),
            calls=self._extract_calls(tree),
            strings=self._extract_strings(tree),
            language="python",
        )

class JavaParser(TreeSitterBaseParser):
    def parse(self, source: str) -> ParseResult:
        tree = self._parser.parse(bytes(source, "utf-8"))
        return ParseResult(
            imports=self.extract_imports(tree.root_node, source),
            classes=self.extract_classes(tree.root_node, source),
            # ... misma estructura
            language="java",
        )
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Abstracción limpia | Los checkers solo conocen `ParseResult`, no AST nativos |
| Tipado fuerte | `ParsedFunction`, `ParsedCall` son dataclasses con atributos definidos |
| Responsabilidad única | Los parsers extraen; los checkers analizan |
| Testeable | Se puede crear un `ParseResult` de prueba sin parsear código real |
| Extensible | Añadir `ParsedDecorator` no rompe los parsers existentes |

---

## 36. Factory function frente a dispatcher manual para parsers

### Problema

El `StaticAnalyzer` necesita obtener el parser correcto según la extensión del archivo. Se necesita un mecanismo de selección que sea fácil de extender.

### Alternativa evaluada: Switch/if-elif en StaticAnalyzer

```python
class StaticAnalyzer:
    def _get_parser(self, file_path):
        ext = file_path.suffix.lower()
        if ext == ".py":
            return PythonParser()
        elif ext == ".java":
            return JavaParser()
        elif ext in {".js", ".ts", ".tsx"}:
            return JSParser()
        elif ext == ".cs":
            return CSharpParser()
        return None
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Acoplamiento | `StaticAnalyzer` conoce todos los parsers concretos |
| Imports dispersos | El analizador importa cada parser individualmente |
| Duplicación | Si otro módulo necesita parsers, reimplementa el switch |
| No testeable aislado | No se puede mockear la selección de parser |

### Solución elegida: Factory function en módulo de parsers

```python
# gtaa_validator/parsers/treesitter_base.py

def get_parser_for_file(file_path: Path):
    """
    Factory function para obtener el parser correcto basado en la extensión.

    Args:
        file_path: Ruta al archivo

    Returns:
        Parser apropiado (PythonParser, JavaParser, JSParser, CSharpParser) o None
    """
    extension = file_path.suffix.lower()

    # Python usa parser nativo (no tree-sitter)
    if extension == ".py":
        from gtaa_validator.parsers.python_parser import PythonParser
        return PythonParser()

    language = TreeSitterBaseParser.get_language_for_extension(extension)

    if language is None:
        return None

    # Importar el parser específico (tree-sitter)
    if language == "java":
        from gtaa_validator.parsers.java_parser import JavaParser
        return JavaParser()
    elif language in ("javascript", "typescript"):
        from gtaa_validator.parsers.js_parser import JSParser
        return JSParser(language)
    elif language == "c_sharp":
        from gtaa_validator.parsers.csharp_parser import CSharpParser
        return CSharpParser()

    return None
```

Uso en `StaticAnalyzer`:

```python
from gtaa_validator.parsers import get_parser_for_file

class StaticAnalyzer:
    def _check_file(self, file_path):
        parser = get_parser_for_file(file_path)
        if parser is None:
            return []

        result = parser.parse(source)
        # ... pasar result a checkers
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Desacoplamiento | `StaticAnalyzer` solo conoce la factory function |
| Imports lazy | Los parsers se importan solo cuando se necesitan |
| Punto único de extensión | Añadir lenguaje = modificar solo `get_parser_for_file()` |
| Testeable | Se puede mockear `get_parser_for_file` en tests |
| Reutilizable | Cualquier módulo puede usar la factory function |

**Patrón Factory Method:**

Esta implementación sigue el patrón Factory Method: un método que encapsula la creación de objetos, permitiendo que las subclases (o en este caso, la lógica interna) decidan qué clase instanciar.

```
        get_parser_for_file(file_path)
                    │
                    ▼
    ┌───────────────────────────────────┐
    │   Decisión basada en extensión    │
    └───────────────────────────────────┘
        │         │         │         │
        ▼         ▼         ▼         ▼
    Python    Java      JS/TS     C#
    Parser    Parser    Parser    Parser
```

---

## 37. Python AST nativo frente a tree-sitter para Python

### Problema

Con la adopción de `tree-sitter-language-pack` para Java, JS/TS y C#, surge la pregunta: ¿debería Python también usar tree-sitter para mantener uniformidad, o seguir usando el módulo `ast` nativo?

### Alternativa evaluada: tree-sitter para todos los lenguajes (incluyendo Python)

```python
from tree_sitter_language_pack import get_parser

class PythonParser(TreeSitterBaseParser):
    def __init__(self):
        super().__init__("python")  # tree-sitter python
```

**Motivos de descarte:**

| Problema | Descripción |
|----------|-------------|
| Dependencia innecesaria | Python ya incluye `ast` en la biblioteca estándar |
| Rendimiento | `ast.parse()` es más rápido que tree-sitter para Python |
| Madurez | El módulo `ast` está extremadamente probado y es el estándar de facto |
| Tipo de nodos | Los checkers ya usaban `ast.FunctionDef`, `ast.Call`, etc. |
| Complejidad añadida | tree-sitter requiere queries de sintaxis; `ast.walk()` es más simple |

### Solución elegida: ast nativo para Python, tree-sitter para los demás

```python
# gtaa_validator/parsers/python_parser.py
import ast

class PythonParser:
    """Parser Python usando ast nativo (stdlib)."""

    def parse(self, source: str) -> ParseResult:
        tree = ast.parse(source)
        return ParseResult(
            imports=self._extract_imports(tree),
            classes=self._extract_classes(tree),
            functions=self._extract_functions(tree),
            calls=self._extract_calls(tree),
            strings=self._extract_strings(tree),
            language="python",
        )

    def _extract_calls(self, tree) -> List[ParsedCall]:
        """Extrae llamadas usando ast.walk() nativo."""
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    calls.append(ParsedCall(
                        object_name=self._get_object_name(node.func.value),
                        method_name=node.func.attr,
                        line=node.lineno,
                    ))
        return calls
```

**Justificación:**

| Ventaja | Descripción |
|---------|-------------|
| Zero dependencias extra | `ast` es parte de Python stdlib |
| Código existente reutilizado | Los visitors AST de Fase 2-8 se adaptaron fácilmente |
| Rendimiento óptimo | `ast.parse()` es código C optimizado |
| Familiaridad | El equipo ya conocía `ast` de fases anteriores |
| Consistencia de salida | `PythonParser.parse()` produce `ParseResult` igual que los demás |

**Arquitectura híbrida:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PARSERS                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐      ┌─────────────────────────────────────────┐   │
│  │  PythonParser   │      │       TreeSitterBaseParser              │   │
│  │  (ast nativo)   │      │  ┌──────────┬──────────┬──────────┐    │   │
│  │                 │      │  │JavaParser│ JSParser │CSharpParser│   │   │
│  │  import ast     │      │  │          │          │           │    │   │
│  │  ast.parse()    │      │  │ tree-sitter-language-pack       │    │   │
│  │  ast.walk()     │      │  └──────────┴──────────┴──────────┘    │   │
│  └────────┬────────┘      └──────────────────┬──────────────────────┘   │
│           │                                   │                          │
│           └───────────────┬───────────────────┘                          │
│                           │                                              │
│                           ▼                                              │
│                    ┌─────────────┐                                       │
│                    │ ParseResult │  ◄── Interfaz común                   │
│                    └─────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

**Principio aplicado — Pragmatismo sobre uniformidad:**

Aunque usar tree-sitter para todos los lenguajes hubiera sido más "uniforme", la decisión pragmática fue:
- Usar la mejor herramienta para cada lenguaje
- Python → `ast` (stdlib, maduro, conocido)
- Java/JS/C# → tree-sitter (única opción viable sin dependencias múltiples)

La uniformidad se logra en la **interfaz de salida** (`ParseResult`), no en la implementación interna.

---

## Resumen de decisiones

| Decisión | Solución elegida | Alternativa descartada | Justificación principal |
|----------|-----------------|----------------------|------------------------|
| Análisis de código | AST (`ast.parse`) | Mapas anidados / Regex | Contexto jerárquico, robustez, estándar de Python |
| Recorrido del AST | Patrón Visitor | `ast.walk()` con bucles | Estado contextual, orden de recorrido, extensibilidad |
| Organización de checkers | Patrón Strategy | Clase monolítica | Tests aislados, Open/Closed, responsabilidad única |
| Orquestación | Patrón Facade | Invocación directa | Encapsulación, punto único de entrada |
| Modelos de datos | Dataclasses + Enums | Diccionarios | Seguridad de tipos, auto-poblado, serialización controlada |
| Niveles de verificación | Proyecto + Archivo | Solo archivo | `StructureChecker` requiere vista global del proyecto |
| Parseo del AST | Una vez por archivo | Una vez por checker | Elimina trabajo redundante, retrocompatible |
| Paradigma principal | POO | Funcional | Los patrones de diseño requieren estado mutable y polimorfismo |
| Modelo LLM | Gemini 2.5 Flash Lite (free) | Claude, GPT-4o, DeepSeek | Gratuito, capacidad suficiente para PoC, sin factura |
| SDK de LLM | google-genai (nativo) | openai SDK / REST directo | SDK oficial, sin capas de compatibilidad, system instruction nativa |
| Interfaz LLM | Duck typing + Union | ABC (Abstract Base Class) | Solo 2 implementaciones, sin herencia retroactiva, Python idiomático |
| Errores de API | Silencioso (try/except → []) | Propagar excepciones | Preserva análisis estático, degradación elegante, free tier friendly |
| Configuración API key | Variable de entorno + .env | Flag CLI / fichero config | Estándar de la industria, seguro, CI/CD compatible, fallback a mock |
| Excepciones genéricas | AST (`ExceptHandler`) | Regex sobre source | Preciso, ignora strings/comentarios, extensible |
| Config hardcodeada | Regex compiladas (clase) | AST de strings | Cobertura uniforme (URLs + sleeps + paths), compilación única |
| Estado mutable compartido | `iter_child_nodes` + `walk` | Solo `ast.walk` | Sin falsos positivos en variables locales, cobertura completa |
| Nuevas violaciones LLM | Ampliar prompt existente | Prompts separados | Misma cantidad de llamadas API, contexto compartido |
| Detección de asserts mock | Búsqueda textual | AST visitor | Cobertura amplia (assert + assertEqual + assert_called), simple |
| Clasificación de archivos | Per-file | Per-project | Granularidad máxima, proyectos mixtos reales |
| Scoring de clasificación | Pesos diferenciados (5/2/3) | Reglas binarias if/elif | Combina señales débiles, extensible |
| Archivos mixtos (API+UI) | UI siempre gana | Score mayor gana | Sin falsos negativos, principio de precaución |
| Detección auto-wait | Automática + YAML complemento | Solo YAML manual | Zero config para Playwright, extensible |
| Configuración de reglas | `.gtaa.yaml` dedicado | `.env` / `pyproject.toml` | Semántico, commitable, agnóstico al lenguaje |
| Parseo YAML | Degradación elegante (defaults) | Fallo estricto (raise) | Zero config, robusto, consistente con ADR 15 |
| Parser Gherkin | Regex propio | gherkin-official (dependencia) | Sin dependencias, ligero, control total |
| Herencia And/But | Rastreo de keyword efectivo | Búsqueda literal "Then" | Semántica correcta de Gherkin |
| Detección step defs | Path + validación AST | Solo AST | Filtrado rápido en can_check(), convención estándar |
| Duplicados step pattern | check_project cross-file | Detección en check() por archivo | Idempotente, vista global, reporte en archivo correcto |
| Detalles implementación | Regex específicas por tipo | Lista de palabras prohibidas | Precisión, mínimos falsos positivos, cobertura amplia |
| Parsing multilenguaje | tree-sitter-language-pack | Parsers separados por lenguaje | Una dependencia, API unificada, 165+ lenguajes, pre-built wheels |
| Organización checkers multilenguaje | Checkers language-agnostic | Un checker por lenguaje | DRY, mantenimiento centralizado, consistencia, Open/Closed |
| Interfaz de datos | ParseResult unificado | AST nativo por lenguaje | Abstracción limpia, tipado fuerte, responsabilidad única |
| Selección de parser | Factory function | Switch en StaticAnalyzer | Desacoplamiento, imports lazy, punto único de extensión |
| Parser Python | ast nativo (stdlib) | tree-sitter para Python | Zero deps extra, rendimiento, código existente reutilizado |

---

*Última actualización: 4 de febrero de 2026*
