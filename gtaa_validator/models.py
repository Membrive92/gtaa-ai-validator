"""
Modelos de datos para gTAA Validator.

Este módulo define las estructuras de datos principales usadas en el proceso de validación:
- Violation: Representa una única violación arquitectónica encontrada en el código
- Report: Agrega todas las violaciones y metadatos de un análisis de proyecto
- Severity: Enumeración de niveles de severidad de violaciones
- ViolationType: Enumeración de tipos de violación gTAA

Estos modelos son utilizados por analizadores, checkers y reportadores.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional
from datetime import datetime


class Severity(Enum):
    """
    Niveles de severidad para violaciones arquitectónicas gTAA.

    CRITICAL: Viola principios fundamentales de gTAA (ej. llamadas directas a Selenium en tests)
    HIGH: Problema arquitectónico significativo (ej. datos de test hardcodeados)
    MEDIUM: Problema de calidad moderado (ej. lógica de negocio en page objects)
    LOW: Problema menor de calidad de código (ej. convenciones de nomenclatura pobres)
    """
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    def get_score_penalty(self) -> int:
        """
        Devuelve la penalización de puntuación para este nivel de severidad.
        Se usa para calcular la puntuación general de cumplimiento (0-100).
        """
        penalties = {
            Severity.CRITICAL: 10,
            Severity.HIGH: 5,
            Severity.MEDIUM: 2,
            Severity.LOW: 1
        }
        return penalties[self]

    def __lt__(self, other):
        """Habilitar ordenación por severidad (CRITICAL > HIGH > MEDIUM > LOW)."""
        if not isinstance(other, Severity):
            return NotImplemented
        severity_order = {
            Severity.CRITICAL: 4,
            Severity.HIGH: 3,
            Severity.MEDIUM: 2,
            Severity.LOW: 1
        }
        return severity_order[self] < severity_order[other]


class ViolationType(Enum):
    """
    Tipos de violaciones arquitectónicas gTAA.

    Cada tipo de violación corresponde a un principio específico de gTAA:
    - Separación de capas (Definición, Adaptación, Ejecución)
    - Externalización de datos
    - Calidad y mantenibilidad del código

    FASE 2: Solo se implementó ADAPTATION_IN_DEFINITION
    FASE 3: Se detectan todos los tipos de violación
    """

    # Violaciones CRÍTICAS - Principios fundamentales de gTAA
    ADAPTATION_IN_DEFINITION = "ADAPTATION_IN_DEFINITION"  # Selenium/Playwright en archivos de test
    MISSING_LAYER_STRUCTURE = "MISSING_LAYER_STRUCTURE"    # Faltan directorios tests/, pages/

    # Violaciones de severidad ALTA
    HARDCODED_TEST_DATA = "HARDCODED_TEST_DATA"            # Emails, URLs hardcodeados en tests
    ASSERTION_IN_POM = "ASSERTION_IN_POM"                  # Aserciones en Page Object Methods
    FORBIDDEN_IMPORT = "FORBIDDEN_IMPORT"                  # Imports de capa incorrecta

    # Violaciones de severidad MEDIA
    BUSINESS_LOGIC_IN_POM = "BUSINESS_LOGIC_IN_POM"        # Lógica de negocio en Page Objects
    DUPLICATE_LOCATOR = "DUPLICATE_LOCATOR"                # Mismo localizador en múltiples sitios
    LONG_TEST_FUNCTION = "LONG_TEST_FUNCTION"              # Tests >50 líneas

    # Violaciones de severidad BAJA
    POOR_TEST_NAMING = "POOR_TEST_NAMING"                  # Nombres genéricos de test (test_1, test_2)

    # Violaciones estáticas adicionales (FASE 6)
    BROAD_EXCEPTION_HANDLING = "BROAD_EXCEPTION_HANDLING"    # except Exception genérico en tests
    HARDCODED_CONFIGURATION = "HARDCODED_CONFIGURATION"      # URLs, timeouts, paths hardcodeados
    SHARED_MUTABLE_STATE = "SHARED_MUTABLE_STATE"            # Variables mutables compartidas entre tests

    # Violaciones semánticas (FASE 5 — detectadas por LLM)
    UNCLEAR_TEST_PURPOSE = "UNCLEAR_TEST_PURPOSE"            # Test sin propósito claro
    PAGE_OBJECT_DOES_TOO_MUCH = "PAGE_OBJECT_DOES_TOO_MUCH" # Page Object con demasiadas responsabilidades
    IMPLICIT_TEST_DEPENDENCY = "IMPLICIT_TEST_DEPENDENCY"    # Tests dependientes del orden de ejecución
    MISSING_WAIT_STRATEGY = "MISSING_WAIT_STRATEGY"          # Sin esperas para operaciones async

    # Violaciones semánticas adicionales (FASE 6 — detectadas por LLM)
    MISSING_AAA_STRUCTURE = "MISSING_AAA_STRUCTURE"          # Test sin estructura Arrange-Act-Assert
    MIXED_ABSTRACTION_LEVEL = "MIXED_ABSTRACTION_LEVEL"      # Keywords de negocio con selectores directos

    # Violaciones BDD/Gherkin (FASE 8)
    GHERKIN_IMPLEMENTATION_DETAIL = "GHERKIN_IMPLEMENTATION_DETAIL"  # Detalles técnicos en .feature
    STEP_DEF_DIRECT_BROWSER_CALL = "STEP_DEF_DIRECT_BROWSER_CALL"  # Browser API en step definitions
    STEP_DEF_TOO_COMPLEX = "STEP_DEF_TOO_COMPLEX"                  # Step definition > 15 líneas
    MISSING_THEN_STEP = "MISSING_THEN_STEP"                        # Scenario sin step Then
    DUPLICATE_STEP_PATTERN = "DUPLICATE_STEP_PATTERN"              # Misma regex en múltiples steps

    def get_severity(self) -> Severity:
        """Devuelve el nivel de severidad para este tipo de violación."""
        severity_map = {
            # Crítica
            ViolationType.ADAPTATION_IN_DEFINITION: Severity.CRITICAL,
            ViolationType.MISSING_LAYER_STRUCTURE: Severity.CRITICAL,

            # Alta
            ViolationType.HARDCODED_TEST_DATA: Severity.HIGH,
            ViolationType.ASSERTION_IN_POM: Severity.HIGH,
            ViolationType.FORBIDDEN_IMPORT: Severity.HIGH,

            # Media
            ViolationType.BUSINESS_LOGIC_IN_POM: Severity.MEDIUM,
            ViolationType.DUPLICATE_LOCATOR: Severity.MEDIUM,
            ViolationType.LONG_TEST_FUNCTION: Severity.MEDIUM,
            ViolationType.BROAD_EXCEPTION_HANDLING: Severity.MEDIUM,

            # Alta (Fase 6)
            ViolationType.HARDCODED_CONFIGURATION: Severity.HIGH,
            ViolationType.SHARED_MUTABLE_STATE: Severity.HIGH,

            # Baja
            ViolationType.POOR_TEST_NAMING: Severity.LOW,

            # Semánticas (Fase 5)
            ViolationType.UNCLEAR_TEST_PURPOSE: Severity.MEDIUM,
            ViolationType.PAGE_OBJECT_DOES_TOO_MUCH: Severity.HIGH,
            ViolationType.IMPLICIT_TEST_DEPENDENCY: Severity.HIGH,
            ViolationType.MISSING_WAIT_STRATEGY: Severity.MEDIUM,

            # Semánticas (Fase 6)
            ViolationType.MISSING_AAA_STRUCTURE: Severity.MEDIUM,
            ViolationType.MIXED_ABSTRACTION_LEVEL: Severity.MEDIUM,

            # BDD/Gherkin (Fase 8)
            ViolationType.GHERKIN_IMPLEMENTATION_DETAIL: Severity.HIGH,
            ViolationType.STEP_DEF_DIRECT_BROWSER_CALL: Severity.CRITICAL,
            ViolationType.STEP_DEF_TOO_COMPLEX: Severity.MEDIUM,
            ViolationType.MISSING_THEN_STEP: Severity.MEDIUM,
            ViolationType.DUPLICATE_STEP_PATTERN: Severity.LOW,
        }
        return severity_map[self]

    def get_description(self) -> str:
        """Devuelve una descripción legible de este tipo de violación."""
        descriptions = {
            ViolationType.ADAPTATION_IN_DEFINITION:
                "El código de test llama directamente a Selenium/Playwright en lugar de usar Page Objects",
            ViolationType.MISSING_LAYER_STRUCTURE:
                "El proyecto carece de la estructura de capas gTAA adecuada (directorios tests/, pages/)",
            ViolationType.HARDCODED_TEST_DATA:
                "Los datos de test están hardcodeados en lugar de externalizados en archivos de datos",
            ViolationType.ASSERTION_IN_POM:
                "El Page Object contiene aserciones (solo deben estar en la capa de test)",
            ViolationType.FORBIDDEN_IMPORT:
                "El archivo importa de una capa prohibida (viola la separación de capas)",
            ViolationType.BUSINESS_LOGIC_IN_POM:
                "El Page Object contiene lógica de negocio (debe estar en una capa separada)",
            ViolationType.DUPLICATE_LOCATOR:
                "El mismo localizador está definido en múltiples Page Objects",
            ViolationType.LONG_TEST_FUNCTION:
                "La función de test es demasiado larga (>50 líneas), reduciendo la mantenibilidad",
            ViolationType.POOR_TEST_NAMING:
                "La función de test tiene un nombre genérico (test_1, test_2, etc.)",
            ViolationType.BROAD_EXCEPTION_HANDLING:
                "El test usa except genérico (except: o except Exception:) que oculta fallos reales",
            ViolationType.HARDCODED_CONFIGURATION:
                "Configuración hardcodeada (URLs, timeouts, sleeps) que debería externalizarse",
            ViolationType.SHARED_MUTABLE_STATE:
                "Estado mutable compartido a nivel de módulo que crea dependencias entre tests",

            # Semánticas (Fase 5)
            ViolationType.UNCLEAR_TEST_PURPOSE:
                "El test no tiene un propósito claro: nombre genérico y sin docstring explicativa",
            ViolationType.PAGE_OBJECT_DOES_TOO_MUCH:
                "El Page Object tiene demasiadas responsabilidades (>10 métodos públicos)",
            ViolationType.IMPLICIT_TEST_DEPENDENCY:
                "El test depende de estado global o variables a nivel de módulo, creando dependencias implícitas",
            ViolationType.MISSING_WAIT_STRATEGY:
                "Interacción con UI sin espera explícita previa, puede causar flakiness",

            # Semánticas (Fase 6)
            ViolationType.MISSING_AAA_STRUCTURE:
                "El test no sigue la estructura Arrange-Act-Assert, dificultando su comprensión",
            ViolationType.MIXED_ABSTRACTION_LEVEL:
                "El método mezcla keywords de negocio con selectores de UI directos (XPath, CSS)",

            # BDD/Gherkin (Fase 8)
            ViolationType.GHERKIN_IMPLEMENTATION_DETAIL:
                "El archivo .feature contiene detalles de implementación (XPath, CSS, URLs, SQL) "
                "que deberían estar solo en step definitions",
            ViolationType.STEP_DEF_DIRECT_BROWSER_CALL:
                "La step definition llama directamente a APIs del navegador en lugar de usar Page Objects",
            ViolationType.STEP_DEF_TOO_COMPLEX:
                "La step definition es demasiado compleja (>15 líneas), debería delegar a Page Objects",
            ViolationType.MISSING_THEN_STEP:
                "El Scenario no tiene step Then (sin verificación de resultado esperado)",
            ViolationType.DUPLICATE_STEP_PATTERN:
                "La misma expresión regular de step está definida en múltiples archivos",
        }
        return descriptions[self]

    def get_recommendation(self) -> str:
        """Devuelve una recomendación sobre cómo corregir esta violación."""
        recommendations = {
            ViolationType.ADAPTATION_IN_DEFINITION:
                "Crear Page Objects que encapsulen las interacciones con Selenium/Playwright. "
                "El código de test debe llamar a page.login() en lugar de driver.find_element().",
            ViolationType.MISSING_LAYER_STRUCTURE:
                "Organizar el proyecto con: tests/ (definiciones de test), pages/ (page objects), "
                "data/ (datos de test), utils/ (utilidades).",
            ViolationType.HARDCODED_TEST_DATA:
                "Mover los datos de test a archivos externos (JSON, YAML, CSV) o fixtures. "
                "Mantener los tests DRY y orientados a datos.",
            ViolationType.ASSERTION_IN_POM:
                "Eliminar las aserciones de los Page Objects. Los Page Objects solo deben interactuar "
                "con la UI y devolver datos. Dejar que los tests verifiquen los datos.",
            ViolationType.FORBIDDEN_IMPORT:
                "Seguir la separación de capas gTAA: Tests importan Pages, Pages importan Utils, "
                "pero nunca al revés.",
            ViolationType.BUSINESS_LOGIC_IN_POM:
                "Extraer la lógica de negocio a clases de servicio/helper separadas. "
                "Los Page Objects solo deben manejar interacciones con la UI.",
            ViolationType.DUPLICATE_LOCATOR:
                "Crear una clase base de página o repositorio de localizadores. Definir cada localizador "
                "una sola vez y reutilizar entre Page Objects.",
            ViolationType.LONG_TEST_FUNCTION:
                "Dividir los tests largos en funciones de test más pequeñas y enfocadas. Cada test debe "
                "verificar un comportamiento específico.",
            ViolationType.POOR_TEST_NAMING:
                "Usar nombres descriptivos: test_usuario_puede_hacer_login_con_credenciales_validas() "
                "en lugar de test_1().",
            ViolationType.BROAD_EXCEPTION_HANDLING:
                "Capturar excepciones específicas (ValueError, TimeoutError, etc.) en lugar de "
                "except genérico. Los tests deben fallar visiblemente ante errores inesperados.",
            ViolationType.HARDCODED_CONFIGURATION:
                "Externalizar configuración a variables de entorno, fixtures de pytest, o archivos "
                "de configuración. Usar conftest.py para URLs base y timeouts.",
            ViolationType.SHARED_MUTABLE_STATE:
                "Eliminar variables mutables a nivel de módulo. Usar fixtures de pytest con scope "
                "apropiado para compartir estado de forma controlada.",

            # Semánticas (Fase 5)
            ViolationType.UNCLEAR_TEST_PURPOSE:
                "Añadir un docstring que explique qué valida el test y por qué. "
                "El nombre debe describir el comportamiento esperado.",
            ViolationType.PAGE_OBJECT_DOES_TOO_MUCH:
                "Dividir el Page Object en componentes más pequeños siguiendo el patrón "
                "Component Object. Cada clase debe representar una sección de la página.",
            ViolationType.IMPLICIT_TEST_DEPENDENCY:
                "Eliminar dependencias de estado global. Usar fixtures de pytest para setup/teardown. "
                "Cada test debe ser independiente y ejecutable en cualquier orden.",
            ViolationType.MISSING_WAIT_STRATEGY:
                "Añadir esperas explícitas (WebDriverWait, expect) antes de interacciones con elementos. "
                "Evitar time.sleep() y preferir esperas condicionales.",

            # Semánticas (Fase 6)
            ViolationType.MISSING_AAA_STRUCTURE:
                "Estructurar el test en tres bloques claros: Arrange (preparar datos), "
                "Act (ejecutar acción) y Assert (verificar resultado). Separar con líneas en blanco.",
            ViolationType.MIXED_ABSTRACTION_LEVEL:
                "Separar los selectores de UI en métodos privados o propiedades del Page Object. "
                "Los métodos públicos deben usar nombres de negocio sin exponer detalles de implementación.",

            # BDD/Gherkin (Fase 8)
            ViolationType.GHERKIN_IMPLEMENTATION_DETAIL:
                "Reescribir los steps usando lenguaje de negocio. En lugar de "
                "'When I click on //div[@id=\"submit\"]', usar 'When I submit the form'. "
                "Los detalles técnicos pertenecen a las step definitions.",
            ViolationType.STEP_DEF_DIRECT_BROWSER_CALL:
                "Crear Page Objects que encapsulen las interacciones del navegador. "
                "Los step definitions deben llamar a page.login() en lugar de driver.find_element().",
            ViolationType.STEP_DEF_TOO_COMPLEX:
                "Extraer la lógica a métodos de Page Object. Los step definitions deben ser "
                "delegadores simples que conectan Gherkin con la capa de adaptación.",
            ViolationType.MISSING_THEN_STEP:
                "Añadir al menos un step Then que verifique el resultado esperado. "
                "Un Scenario sin verificación no valida ningún comportamiento.",
            ViolationType.DUPLICATE_STEP_PATTERN:
                "Consolidar los step definitions duplicados en un único archivo compartido. "
                "Usar un directorio steps/common/ para steps reutilizables.",
        }
        return recommendations[self]


@dataclass
class Violation:
    """
    Representa una única violación arquitectónica gTAA detectada en el código.

    Atributos:
        violation_type: Tipo de violación (enum)
        severity: Nivel de severidad (enum)
        file_path: Ruta al archivo que contiene la violación
        line_number: Número de línea donde ocurre la violación (si aplica)
        message: Mensaje detallado explicando la violación
        code_snippet: Fragmento de código opcional mostrando la violación
        recommendation: Cómo corregir esta violación
        ai_suggestion: Sugerencia generada por análisis semántico LLM (opcional)
    """
    violation_type: ViolationType
    severity: Severity
    file_path: Path
    line_number: Optional[int] = None
    message: str = ""
    code_snippet: Optional[str] = None
    recommendation: str = ""
    ai_suggestion: Optional[str] = None

    def __post_init__(self):
        """
        Auto-rellenar campos desde el tipo de violación si no se proporcionan.
        Esto asegura consistencia en todas las violaciones.
        """
        # Si la severidad no se establece explícitamente, obtener del tipo de violación
        if not self.severity:
            self.severity = self.violation_type.get_severity()

        # Si no se proporciona recomendación, obtener la recomendación por defecto
        if not self.recommendation:
            self.recommendation = self.violation_type.get_recommendation()

        # Si no se proporciona mensaje, usar la descripción de la violación
        if not self.message:
            self.message = self.violation_type.get_description()

    def to_dict(self) -> dict:
        """Convertir violación a diccionario para serialización JSON."""
        return {
            "type": self.violation_type.name,
            "severity": self.severity.value,
            "file": str(self.file_path),
            "line": self.line_number,
            "message": self.message,
            "code_snippet": self.code_snippet,
            "recommendation": self.recommendation,
            "ai_suggestion": self.ai_suggestion,
        }


@dataclass
class Report:
    """
    Agrega todas las violaciones y metadatos de un análisis completo de proyecto.

    Atributos:
        project_path: Directorio raíz del proyecto analizado
        violations: Lista de todas las violaciones detectadas
        files_analyzed: Número de archivos analizados
        timestamp: Cuándo se realizó el análisis
        validator_version: Versión del validador gTAA utilizado
        score: Puntuación de cumplimiento (0-100)
        execution_time_seconds: Tiempo empleado en el análisis
        llm_provider_info: Información del proveedor LLM usado (solo con --ai)
    """
    project_path: Path
    violations: List[Violation] = field(default_factory=list)
    files_analyzed: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    validator_version: str = "0.4.0"
    score: float = 100.0
    execution_time_seconds: float = 0.0
    llm_provider_info: Optional[dict] = None

    def calculate_score(self) -> float:
        """
        Calcular la puntuación de cumplimiento (0-100) basada en las violaciones.

        Fórmula: Comenzar en 100, restar penalización por cada violación.
        La puntuación mínima es 0.
        """
        total_penalty = sum(v.severity.get_score_penalty() for v in self.violations)
        score = max(0.0, 100.0 - total_penalty)
        self.score = score
        return score

    def get_violations_by_severity(self, severity: Severity) -> List[Violation]:
        """Obtener todas las violaciones de un nivel de severidad específico."""
        return [v for v in self.violations if v.severity == severity]

    def get_violation_count_by_severity(self) -> dict:
        """Devolver el recuento de violaciones agrupadas por severidad."""
        return {
            "CRITICAL": len(self.get_violations_by_severity(Severity.CRITICAL)),
            "HIGH": len(self.get_violations_by_severity(Severity.HIGH)),
            "MEDIUM": len(self.get_violations_by_severity(Severity.MEDIUM)),
            "LOW": len(self.get_violations_by_severity(Severity.LOW)),
        }

    def to_dict(self) -> dict:
        """Convertir informe a diccionario para serialización JSON."""
        metadata = {
            "project_path": str(self.project_path),
            "timestamp": self.timestamp.isoformat(),
            "validator_version": self.validator_version,
            "execution_time_seconds": self.execution_time_seconds,
        }
        # Añadir info del proveedor LLM si está disponible
        if self.llm_provider_info:
            metadata["llm_provider"] = self.llm_provider_info

        return {
            "metadata": metadata,
            "summary": {
                "files_analyzed": self.files_analyzed,
                "total_violations": len(self.violations),
                "violations_by_severity": self.get_violation_count_by_severity(),
                "score": self.score,
            },
            "violations": [v.to_dict() for v in self.violations]
        }
