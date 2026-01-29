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

---

*Última actualización: 29 de enero de 2026*
