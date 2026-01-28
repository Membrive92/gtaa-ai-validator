# Decisiones Arquitectónicas del Proyecto

Este documento explica **por qué** se eligió cada decisión técnica del proyecto gTAA AI Validator, comparando con las alternativas descartadas.

---

## 1. ¿Por qué AST y no mapas anidados / regex puro?

### El problema

Necesitamos analizar código Python para detectar violaciones como:
- Test que llaman directamente a `driver.find_element()` en vez de usar Page Objects
- Page Objects que contienen `assert` o lógica de negocio (`if/for/while`)
- Datos hardcoded dentro de funciones de test

### Alternativa descartada: Mapas anidados (diccionarios)

Un enfoque con mapas anidados representaría el código como estructuras tipo:

```python
# Representación manual del código como diccionario
code_map = {
    "functions": {
        "test_login": {
            "calls": ["driver.find_element", "login_page.login"],
            "strings": ["admin@test.com"],
            "lines": [10, 11, 12, ...]
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

**Problemas con este enfoque:**

| Problema | Explicación |
|----------|-------------|
| **Hay que construir el mapa manualmente** | Necesitas parsear el código de todas formas para llenar el diccionario — acabas reimplementando un parser |
| **Estructura rígida** | Cada nuevo tipo de violación requiere cambiar la estructura del mapa |
| **Pierde contexto posicional** | No sabes en qué línea está cada elemento, ni si una llamada está dentro de un `if` o de un método |
| **No distingue contexto** | `driver.find_element()` a nivel de módulo vs dentro de `test_login()` son cosas distintas — un mapa plano no lo captura |
| **Duplica trabajo** | Python ya tiene `ast.parse()` que genera exactamente esta representación, pero completa y correcta |

### Alternativa descartada: Regex puro

```python
# Buscar llamadas a Selenium con regex
import re
violations = re.findall(r'driver\.\w+\(', source_code)
```

**Problemas con regex:**

| Problema | Ejemplo |
|----------|---------|
| **Falsos positivos en comentarios** | `# driver.find_element(...)` se detectaría como violación |
| **Falsos positivos en strings** | `"driver.find_element"` como dato de test |
| **No entiende contexto** | No sabe si estás dentro de una función test o una función helper |
| **No distingue clases** | No puede saber si un `assert` está en un Page Object o en un test |
| **Frágil ante formato** | `driver . find_element()` o llamadas en múltiples líneas rompen la regex |
| **Mantenimiento costoso** | Cada patrón nuevo es una regex nueva que puede interferir con las existentes |

### Solución elegida: AST (Abstract Syntax Tree)

```python
tree = ast.parse(source_code)
visitor = BrowserAPICallVisitor()
visitor.visit(tree)
```

**Ventajas del AST:**

| Ventaja | Explicación |
|---------|-------------|
| **Ignora comentarios y strings automáticamente** | El parser solo genera nodos para código ejecutable real |
| **Contexto jerárquico nativo** | Cada nodo sabe si está dentro de una función, clase o módulo |
| **Información posicional** | Cada nodo tiene `lineno` y `col_offset` — podemos reportar la línea exacta |
| **Estándar de Python** | `ast` es módulo de la biblioteca estándar, sin dependencias externas |
| **Extensible** | Añadir un nuevo visitor para detectar otro patrón no afecta a los existentes |
| **Robusto** | No importa cómo formatees el código — el AST es el mismo |

### Ejemplo concreto: detectar `assert` en Page Objects

```python
# Con regex (frágil):
if re.search(r'^\s+assert\s', line):
    # ¿Estamos en una clase? ¿En un método? No lo sabemos.

# Con AST (robusto):
class _AssertionVisitor(ast.NodeVisitor):
    def visit_ClassDef(self, node):
        self._in_class = True       # Sabemos que estamos en una clase
        self.generic_visit(node)
        self._in_class = False

    def visit_FunctionDef(self, node):
        if self._in_class:
            self._in_method = True   # Sabemos que estamos en un método
            self.generic_visit(node)
            self._in_method = False

    def visit_Assert(self, node):
        if self._in_class and self._in_method:
            # SOLO reportamos si el assert está en un método de clase
            self.violations.append(...)
```

El AST nos da la jerarquía `Clase → Método → Assert` de forma natural, sin tener que rastrear indentación ni contar llaves.

### ¿Cuándo sí usamos regex?

Regex se usa como **complemento** del AST en casos específicos donde es la herramienta correcta:

- **Detección de locators**: `By.ID, "login-btn"` — patrón textual dentro de strings que el AST ya extrajo
- **Datos hardcoded**: emails, URLs, teléfonos — patrones dentro de nodos `ast.Constant` que el AST ya aisló
- **Nombres genéricos**: `test_1`, `test_a` — patrón sobre el nombre de la función, no sobre código

La combinación **AST para estructura + regex para contenido de strings** es lo que da robustez al análisis.

---

## 2. ¿Por qué el patrón Visitor y no simples bucles?

### Alternativa descartada: `ast.walk()` con condicionales

```python
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
        for child in ast.walk(node):
            if isinstance(node, ast.Call):
                # ¿Es una llamada a Selenium?
                ...
```

**Problemas:**
- `ast.walk()` recorre en orden arbitrario — no garantiza que proceses el padre antes del hijo
- Pierdes el contexto "estoy dentro de esta función" cuando procesas nodos anidados
- Código rápidamente se convierte en bucles anidados difíciles de mantener

### Solución elegida: Visitor Pattern

```python
class BrowserAPICallVisitor(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        self._current_function = node.name
        self.generic_visit(node)       # Procesa hijos DENTRO del contexto
        self._current_function = None

    def visit_Call(self, node):
        if self._current_function:     # Sabemos en qué función estamos
            self._check_call(node)
        self.generic_visit(node)
```

**Ventajas:**
- **Recorrido en profundidad ordenado**: el padre siempre se visita antes que sus hijos
- **Estado contextual**: variables como `_current_function` o `_in_class` se mantienen correctamente durante el recorrido
- **Separación de responsabilidades**: cada `visit_X` maneja exactamente un tipo de nodo
- **Extensibilidad**: añadir detección de un nuevo tipo de nodo es añadir un método `visit_NuevoNodo()`
- **Patrón estándar**: el módulo `ast` de Python está diseñado para funcionar con visitors

---

## 3. ¿Por qué el patrón Strategy (BaseChecker) y no un único checker monolítico?

### Alternativa descartada: Un solo archivo con toda la lógica

```python
class Analyzer:
    def check(self, file):
        # 500+ líneas con todos los checks mezclados
        self._check_selenium_calls(file)
        self._check_assertions(file)
        self._check_imports(file)
        self._check_structure(file)
        ...
```

**Problemas:**
- Un archivo de 500+ líneas es difícil de mantener y testear
- No puedes testear un tipo de check aisladamente
- Añadir un nuevo checker requiere modificar la clase existente (viola Open/Closed Principle)
- No puedes reutilizar checkers en otros contextos

### Solución elegida: Strategy Pattern

```
BaseChecker (abstracto)
    ├── DefinitionChecker    → violaciones en tests
    ├── AdaptationChecker    → violaciones en Page Objects
    ├── StructureChecker     → violaciones de estructura
    └── QualityChecker       → violaciones de calidad
```

**Ventajas:**
- **Tests unitarios aislados**: 25 tests para AdaptationChecker sin tocar los otros
- **Open/Closed**: añadir Phase 4 checkers = crear nuevos archivos, sin modificar los existentes
- **Responsabilidad única**: cada checker sabe exactamente qué detectar y qué archivos le interesan (`can_check()`)
- **Composición**: el `StaticAnalyzer` compone checkers como piezas independientes

---

## 4. ¿Por qué Facade (StaticAnalyzer) y no llamar checkers directamente?

### Sin Facade

```python
# El CLI tendría que conocer todos los checkers
checkers = [DefinitionChecker(), AdaptationChecker(), ...]
files = discover_files(path)
violations = []
for f in files:
    for c in checkers:
        if c.can_check(f):
            violations.extend(c.check(f))
# Calcular score, crear report...
```

### Con Facade

```python
# El CLI solo conoce StaticAnalyzer
analyzer = StaticAnalyzer(path)
report = analyzer.analyze()
```

**Ventajas:**
- El CLI no necesita saber cuántos checkers hay ni cómo funcionan
- La lógica de descubrimiento de archivos, filtrado y scoring está encapsulada
- Cuando añadamos fases futuras (AI analyzer, etc.), el CLI no cambia
- Un único punto de entrada para tests de integración

---

## 5. ¿Por qué Dataclasses y no diccionarios para los modelos?

### Alternativa descartada: Diccionarios

```python
violation = {
    "type": "ADAPTATION_IN_DEFINITION",
    "severity": "CRITICAL",
    "line": 42,
    "message": "..."
}
# Fácil de crear, pero...
# violation["typo"] → KeyError en runtime
# violation["severity"] → "CRITICAL" o "critical" o "Critical"?
```

### Solución elegida: Dataclasses + Enums

```python
@dataclass
class Violation:
    violation_type: ViolationType    # Solo valores válidos del enum
    severity: Severity               # AUTO-calculado desde violation_type
    file_path: Path
    line_number: Optional[int]
    message: str
```

**Ventajas:**
- **Type safety**: IDE detecta errores antes de ejecutar
- **Auto-poblado**: `__post_init__` calcula severity y recommendation automáticamente desde el ViolationType
- **Inmutabilidad conceptual**: estructura clara, no se añaden campos arbitrarios
- **Serialización**: `to_dict()` en Report convierte todo a JSON de forma controlada

---

## 6. ¿Por qué checks a dos niveles (proyecto + archivo)?

### El problema

StructureChecker necesita verificar si existen directorios `tests/` y `pages/`. Esto no es una propiedad de ningún archivo individual — es una propiedad del proyecto.

### Solución elegida: `check_project()` + `check()`

```python
class BaseChecker:
    def check(self, file_path) -> List[Violation]:       # Por archivo
        ...
    def check_project(self, project_path) -> List[Violation]:  # Por proyecto
        return []  # Default: no hace nada
```

- `check_project()` se ejecuta una vez antes del bucle de archivos
- `check()` se ejecuta por cada archivo que pasa `can_check()`
- StructureChecker solo implementa `check_project()`; su `can_check()` devuelve `False`
- Los otros 3 checkers solo implementan `check()`

Esto evita forzar un paradigma único para dos necesidades distintas.

---

## 7. ¿Por qué parsear el AST una sola vez por archivo?

### El problema

Cuando múltiples checkers analizan el mismo archivo, cada uno llamaba a `ast.parse()` independientemente:

```python
# ANTES: cada checker parsea por separado
class DefinitionChecker:
    def check(self, file_path):
        source = open(file_path).read()
        tree = ast.parse(source)          # Parse #1
        ...

class QualityChecker:
    def check(self, file_path):
        source = open(file_path).read()
        tree = ast.parse(source)          # Parse #2 (mismo archivo!)
        ...
```

Un archivo test puede ser procesado por `DefinitionChecker` y `QualityChecker` — dos llamadas a `ast.parse()` para el mismo código.

### Solución elegida: Parse único en el Analyzer

```python
# AHORA: StaticAnalyzer parsea una vez y pasa el tree
class StaticAnalyzer:
    def _check_file(self, file_path):
        tree = ast.parse(open(file_path).read())  # Parse UNA vez
        for checker in applicable:
            checker.check(file_path, tree)         # Reutiliza el tree

class BaseChecker:
    def check(self, file_path, tree=None):         # tree opcional
        if tree is None:
            tree = ast.parse(...)                   # Fallback standalone
```

**Ventajas:**
- **Elimina trabajo redundante**: con 4 checkers, un archivo se parseaba hasta 2-3 veces. Ahora solo 1
- **Retrocompatible**: `tree` es opcional — los checkers pueden usarse standalone sin el Analyzer
- **Responsabilidad clara**: el Analyzer gestiona I/O y parsing; los checkers solo analizan el árbol

**Caso especial — AdaptationChecker**: necesita leer el `source_code` (texto raw) para detección de locators con regex. El archivo se lee en el checker, pero no se vuelve a parsear el AST.

**¿Por qué no pasar también el `source_code`?**

Se consideró pasar `(file_path, tree, source_code)` pero solo un checker (AdaptationChecker) necesita el texto raw, y solo para un sub-check (duplicate locators). Añadir un parámetro que 3 de 4 checkers ignoran contamina la interfaz sin beneficio real.

---

## Resumen de decisiones

| Decisión | Elegido | Descartado | Razón principal |
|----------|---------|------------|-----------------|
| Análisis de código | AST | Mapas anidados / Regex | Contexto jerárquico, robustez, estándar de Python |
| Recorrido del AST | Visitor Pattern | ast.walk() con bucles | Estado contextual, orden de recorrido, extensibilidad |
| Organización de checks | Strategy Pattern | Clase monolítica | Tests aislados, Open/Closed, responsabilidad única |
| Orquestación | Facade Pattern | Llamadas directas | Encapsulación, punto único de entrada |
| Modelos de datos | Dataclasses + Enums | Diccionarios | Type safety, auto-poblado, serialización controlada |
| Niveles de check | Proyecto + Archivo | Solo archivo | StructureChecker necesita vista global del proyecto |
| Parsing AST | Una vez por archivo | Por cada checker | Elimina trabajo redundante, retrocompatible |

---

**Última actualización**: 28 Enero 2026
