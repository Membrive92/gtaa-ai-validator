# Proyectos de Ejemplo para gTAA Validator

Este directorio contiene proyectos de ejemplo para demostrar y probar el funcionamiento del validador gTAA.

## Propósito

Los proyectos de ejemplo sirven para:

1. **Demostración**: Mostrar qué detecta el validador y cómo se ven los resultados
2. **Pruebas**: Verificar que el validador funciona correctamente
3. **Documentación**: Ejemplos prácticos de violaciones gTAA vs código correcto
4. **Evaluación académica**: Permitir a los profesores verificar los resultados del TFM

---

## Estructura

```
examples/
├── README.md                                   # Este archivo
├── bad_project/                                # Python — ~45 violaciones gTAA
├── good_project/                               # Python — 0 violaciones (referencia)
├── java_project/                               # Java — Selenium + Cucumber
├── js_project/                                 # JavaScript/TypeScript — Playwright + Cypress
├── csharp_project/                             # C# — NUnit + SpecFlow
├── python_live_project/                        # Python — Proyecto real Playwright
├── Automation-Guide-Selenium-Java-main/        # Java — Proyecto real Selenium (UAT)
└── Automation-Guide-Rest-Assured-Java-master/  # Java — Proyecto real REST Assured (UAT)
```

> **Nota:** Los 5 proyectos pequeños (`bad_project`, `good_project`, `java_project`,
> `js_project`, `csharp_project`) también están incluidos dentro del paquete Python
> en `gtaa_validator/examples/` para que estén disponibles vía `pip install`.
> Se puede acceder a ellos con: `python -m gtaa_validator --examples-path`

---

## Uso

### Analizar proyecto malo

```bash
# Desde el directorio raíz del proyecto gtaa-ai-validator
python -m gtaa_validator examples/bad_project

# Con detalles verbose
python -m gtaa_validator examples/bad_project --verbose
```

**Resultado esperado:**
- 35 violaciones detectadas (múltiples severidades)
- Puntuación: 0.0/100
- Estado: PROBLEMAS CRÍTICOS

### Analizar proyecto bueno

```bash
python -m gtaa_validator examples/good_project

# Con detalles verbose
python -m gtaa_validator examples/good_project --verbose
```

**Resultado esperado:**
- 0 violaciones
- Puntuación: 100.0/100
- Estado: EXCELENTE

---

## Proyecto 1: bad_project

### Descripción

Este proyecto demuestra **código MAL ESTRUCTURADO** que viola los principios de gTAA.
Los tests llaman directamente a las APIs de Selenium y Playwright en lugar de usar Page Objects.

### Archivos

#### `test_login.py` (8 violaciones esperadas)

Este archivo contiene tests de login que usan Selenium directamente.

**Violaciones detalladas:**

| # | Línea | Tipo | Código | Razón |
|---|-------|------|--------|-------|
| 1 | 24 | `ADAPTATION_IN_DEFINITION` | `driver.find_element(By.ID, "username")` | Test llama directamente a Selenium |
| 2 | 25 | `ADAPTATION_IN_DEFINITION` | `driver.find_element(By.ID, "password")` | Test llama directamente a Selenium |
| 3 | 26 | `ADAPTATION_IN_DEFINITION` | `driver.find_element(By.XPATH, "//button[@type='submit']")` | Test llama directamente a Selenium |
| 4 | 34 | `ADAPTATION_IN_DEFINITION` | `driver.find_element(By.CLASS_NAME, "welcome")` | Test llama directamente a Selenium |
| 5 | 46 | `ADAPTATION_IN_DEFINITION` | `driver.find_element(By.ID, "username")` | Test llama directamente a Selenium |
| 6 | 47 | `ADAPTATION_IN_DEFINITION` | `driver.find_element(By.ID, "password")` | Test llama directamente a Selenium |
| 7 | 48 | `ADAPTATION_IN_DEFINITION` | `driver.find_element(By.CSS_SELECTOR, "button.submit-btn")` | Test llama directamente a Selenium |
| 8 | 51 | `ADAPTATION_IN_DEFINITION` | `driver.find_element(By.CLASS_NAME, "error-message")` | Test llama directamente a Selenium |

**Por qué está mal:**
- Los tests en la capa de **Definition** (definición de tests) están haciendo llamadas directas a la capa de **Adaptation** (Selenium/Playwright)
- Según gTAA, los tests deben llamar a Page Objects, no a driver directamente
- Esto hace el código difícil de mantener: si cambia un locator, hay que modificar todos los tests

**Cómo debería ser:**
```python
# MAL ❌
driver.find_element(By.ID, "username").send_keys("user")

# BIEN ✅
login_page.enter_username("user")
```

---

#### `test_search.py` (7 violaciones esperadas)

Este archivo contiene tests de búsqueda que usan Playwright directamente.

**Violaciones detalladas:**

| # | Línea | Tipo | Código | Razón |
|---|-------|------|--------|-------|
| 1 | 18 | `ADAPTATION_IN_DEFINITION` | `page.locator("#search-input")` | Test llama directamente a Playwright |
| 2 | 19 | `ADAPTATION_IN_DEFINITION` | `page.locator("button.search-btn")` | Test llama directamente a Playwright |
| 3 | 22 | `ADAPTATION_IN_DEFINITION` | `page.locator(".search-results")` | Test llama directamente a Playwright |
| 4 | 36 | `ADAPTATION_IN_DEFINITION` | `page.click("#filter-dropdown")` | Test llama directamente a Playwright |
| 5 | 37 | `ADAPTATION_IN_DEFINITION` | `page.click("text=Price: Low to High")` | Test llama directamente a Playwright |
| 6 | 40 | `ADAPTATION_IN_DEFINITION` | `page.wait_for_selector(".filtered-results")` | Test llama directamente a Playwright |
| 7 | 43 | `ADAPTATION_IN_DEFINITION` | `page.locator(".price")` | Test llama directamente a Playwright |

**Por qué está mal:**
- Similar al caso de Selenium: los tests llaman directamente a Playwright
- Viola la separación de capas de gTAA
- Si cambia la estructura de la página, hay que modificar múltiples tests

**Cómo debería ser:**
```python
# MAL ❌
page.locator("#search-input").fill("query")

# BIEN ✅
search_page.enter_search_query("query")
```

---

### Resumen bad_project

**Total violaciones esperadas: 35**

| Severidad | Cantidad |
|-----------|----------|
| CRÍTICA | 16 |
| ALTA | 13 |
| MEDIA | 4 |
| BAJA | 2 |

**Puntuación esperada: 0.0/100**

**Problemas arquitectónicos:**
- ❌ No existe separación de capas (falta directorio tests/)
- ❌ Tests llaman directamente a Selenium/Playwright
- ❌ Page Objects con asserts, imports prohibidos y lógica de negocio
- ❌ Datos hardcoded en tests (emails, URLs, passwords)
- ❌ Nombres genéricos (test_1, test_2) y funciones largas
- ❌ Código no es mantenible ni reutilizable

---

## Proyecto 2: good_project

### Descripción

Este proyecto demuestra **código BIEN ESTRUCTURADO** que sigue los principios de gTAA correctamente.
Usa Page Objects para encapsular todas las interacciones con Selenium.

### Archivos

#### `pages/login_page.py`

Page Object que encapsula todas las interacciones con la página de login.

**Características correctas:**
- ✅ Encapsula todos los locators en un solo lugar
- ✅ Proporciona métodos de alto nivel (`login()`, `enter_username()`)
- ✅ Oculta detalles de implementación de Selenium
- ✅ Facilita mantenimiento: cambio en un solo archivo
- ✅ Reutilizable en múltiples tests

**Estructura:**
```python
class LoginPage:
    def __init__(self, driver):
        self.driver = driver
        # Locators centralizados
        self.username_input = (By.ID, "username")
        ...

    # Métodos de alto nivel
    def login(self, username, password):
        self.enter_username(username)
        self.enter_password(password)
        self.click_submit()
```

---

#### `tests/test_login.py`

Tests que usan el Page Object en lugar de Selenium directamente.

**Características correctas:**
- ✅ Tests solo llaman a métodos del Page Object
- ✅ No hay llamadas directas a `driver.find_element()`
- ✅ Tests son legibles y expresivos
- ✅ Tests son cortos y focalizados
- ✅ Separación clara entre Definition (tests) y Adaptation (Page Objects)

**Estructura de test correcta:**
```python
def test_login_with_valid_credentials():
    driver = webdriver.Chrome()

    # Usa Page Object
    login_page = LoginPage(driver)
    login_page.navigate()
    login_page.login("testuser", "password123")

    # Verifica resultados
    welcome_msg = login_page.get_welcome_message()
    assert "Welcome" in welcome_msg
```

**Sin violaciones porque:**
- No hay llamadas directas a `driver.find_element()` en el test
- No hay llamadas a `page.locator()` en el test
- Todo pasa por el Page Object (`login_page`)

---

### Resumen good_project

**Total violaciones esperadas: 0**

| Severidad | Cantidad |
|-----------|----------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |

**Score esperado: 100.0/100**

**Ventajas arquitectónicas:**
- ✅ Separación clara de capas (Definition y Adaptation)
- ✅ Page Objects encapsulan toda la lógica de Selenium
- ✅ Tests legibles y de alto nivel
- ✅ Código mantenible y reutilizable
- ✅ Cambios en UI solo afectan Page Objects, no tests

---

## Comparación lado a lado

### Test MAL estructurado (bad_project)

```python
def test_login_with_valid_credentials():
    driver = webdriver.Chrome()
    driver.get("https://example.com/login")

    # ❌ Llamadas directas a Selenium
    driver.find_element(By.ID, "username").send_keys("testuser")
    driver.find_element(By.ID, "password").send_keys("password123")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    # ❌ Más llamadas directas
    welcome_message = driver.find_element(By.CLASS_NAME, "welcome").text
    assert "Welcome" in welcome_message

    driver.quit()
```

**Problemas:**
- 4 violaciones CRITICAL en un solo test
- Locators hardcoded
- Difícil de leer y mantener

---

### Test BIEN estructurado (good_project)

```python
def test_login_with_valid_credentials():
    driver = webdriver.Chrome()

    # ✅ Usa Page Object
    login_page = LoginPage(driver)
    login_page.navigate()
    login_page.login("testuser", "password123")

    # ✅ Obtiene datos via Page Object
    welcome_msg = login_page.get_welcome_message()
    assert "Welcome" in welcome_msg

    driver.quit()
```

**Ventajas:**
- 0 violaciones
- Código legible y expresivo
- Fácil de mantener
- Reutilizable

---

## Validación de resultados

Para verificar que el validador funciona correctamente, los resultados deben coincidir con las tablas de este documento.

### Script de prueba

```bash
#!/bin/bash
# test_examples.sh

echo "=== Testing bad_project ==="
python -m gtaa_validator examples/bad_project
echo ""

echo "=== Testing good_project ==="
python -m gtaa_validator examples/good_project
echo ""

echo "=== Testing bad_project (verbose) ==="
python -m gtaa_validator examples/bad_project --verbose
```

### Checklist de validación

Para evaluadores/profesores - verificar que:

- [ ] `bad_project` detecta exactamente **35 violaciones**
- [ ] Violaciones incluyen 9 tipos distintos (4 checkers)
- [ ] Severidades: 16 CRÍTICA, 13 ALTA, 4 MEDIA, 2 BAJA
- [ ] Puntuación de `bad_project` es **0.0/100**
- [ ] `good_project` detecta **0 violaciones**
- [ ] Puntuación de `good_project` es **100.0/100**
- [ ] Modo `--verbose` muestra líneas y código para cada violación
- [ ] Las líneas reportadas coinciden con las tablas de este README

---

## Notas para el TFM

### Metodología de validación

Estos proyectos de ejemplo forman parte de la validación empírica del TFM:

1. **Dataset etiquetado**: Cada violación está documentada con línea exacta y razón
2. **Ground truth**: Sabemos exactamente qué debe detectar (15 violaciones específicas)
3. **Reproducibilidad**: Cualquier evaluador puede ejecutar y verificar resultados
4. **Baseline**: Establece funcionamiento mínimo esperado del validador

### Métricas calculables

Con estos ejemplos se pueden calcular:

- **Precisión**: ¿Las 15 detecciones son correctas? (true positives vs false positives)
- **Recall**: ¿Se detectaron todas las violaciones conocidas? (15/15 = 100%)
- **Exactitud de línea**: ¿Las líneas reportadas son exactas?
- **Tiempo de análisis**: ¿Cuánto tarda en analizar 2 archivos?

---

## Proyectos multi-lenguaje

Además de los proyectos Python (`bad_project`, `good_project`), se incluyen ejemplos en otros lenguajes:

| Proyecto | Lenguaje | Framework | Violaciones esperadas |
|----------|----------|-----------|----------------------|
| `java_project` | Java | Selenium + Cucumber (BDD) | Sí |
| `js_project` | JavaScript/TypeScript | Playwright + Cypress | Sí |
| `csharp_project` | C# | NUnit + SpecFlow (BDD) | Sí |

```bash
python -m gtaa_validator examples/java_project --verbose
python -m gtaa_validator examples/js_project --verbose
python -m gtaa_validator examples/csharp_project --verbose
```

---

## Licencia

Estos ejemplos son parte del proyecto gTAA AI Validator y están bajo licencia MIT.
