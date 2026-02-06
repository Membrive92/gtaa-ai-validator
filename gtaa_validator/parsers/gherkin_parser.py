"""
Parser ligero para archivos Gherkin (.feature).

Extrae la estructura de Features, Scenarios y Steps usando regex.
Gherkin tiene una sintaxis suficientemente regular para no necesitar
una dependencia externa como gherkin-official.

Soporta las keywords principales:
- Feature, Scenario, Scenario Outline
- Given, When, Then, And, But
- Background
- Examples (Scenario Outline)

Fase 8: Soporte BDD para Behave y pytest-bdd.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GherkinStep:
    """Un step individual dentro de un Scenario."""
    keyword: str        # 'Given', 'When', 'Then', 'And', 'But'
    text: str           # Texto del step
    line: int           # Número de línea en el archivo


@dataclass
class GherkinScenario:
    """Un Scenario (o Scenario Outline) dentro de un Feature."""
    name: str
    line: int
    steps: List[GherkinStep] = field(default_factory=list)
    is_outline: bool = False

    @property
    def has_given(self) -> bool:
        return self._has_effective_keyword("Given")

    @property
    def has_when(self) -> bool:
        return self._has_effective_keyword("When")

    @property
    def has_then(self) -> bool:
        return self._has_effective_keyword("Then")

    def _has_effective_keyword(self, keyword: str) -> bool:
        """Verifica si el scenario tiene un step con el keyword efectivo."""
        effective = None
        for step in self.steps:
            if step.keyword in ("Given", "When", "Then"):
                effective = step.keyword
            # And/But heredan el keyword del step anterior
            if effective == keyword:
                return True
        return False


@dataclass
class GherkinFeature:
    """Un Feature file completo."""
    name: str
    line: int
    scenarios: List[GherkinScenario] = field(default_factory=list)
    background: Optional[GherkinScenario] = None


class GherkinParser:
    """
    Parser regex para archivos .feature.

    Extrae Features, Scenarios y Steps de archivos Gherkin
    para análisis estático de violaciones BDD.
    """

    # Regex para líneas significativas de Gherkin
    FEATURE_RE = re.compile(r'^\s*Feature:\s*(.+)', re.IGNORECASE)
    SCENARIO_RE = re.compile(r'^\s*Scenario:\s*(.+)', re.IGNORECASE)
    SCENARIO_OUTLINE_RE = re.compile(r'^\s*Scenario Outline:\s*(.+)', re.IGNORECASE)
    BACKGROUND_RE = re.compile(r'^\s*Background:', re.IGNORECASE)
    STEP_RE = re.compile(r'^\s*(Given|When|Then|And|But)\s+(.+)', re.IGNORECASE)
    EXAMPLES_RE = re.compile(r'^\s*Examples:', re.IGNORECASE)
    TAG_RE = re.compile(r'^\s*@')
    COMMENT_RE = re.compile(r'^\s*#')

    def parse(self, content: str) -> Optional[GherkinFeature]:
        """
        Parsea el contenido de un archivo .feature.

        Args:
            content: Contenido completo del archivo .feature

        Returns:
            GherkinFeature con la estructura parseada, o None si no es válido
        """
        lines = content.splitlines()
        feature = None
        current_scenario = None
        in_background = False

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Ignorar líneas vacías, comentarios y tags
            if not stripped or self.COMMENT_RE.match(line) or self.TAG_RE.match(line):
                continue

            # Feature
            match = self.FEATURE_RE.match(line)
            if match:
                feature = GherkinFeature(name=match.group(1).strip(), line=i)
                continue

            if feature is None:
                continue

            # Background
            if self.BACKGROUND_RE.match(line):
                current_scenario = GherkinScenario(name="Background", line=i)
                feature.background = current_scenario
                in_background = True
                continue

            # Scenario Outline
            match = self.SCENARIO_OUTLINE_RE.match(line)
            if match:
                current_scenario = GherkinScenario(
                    name=match.group(1).strip(), line=i, is_outline=True
                )
                feature.scenarios.append(current_scenario)
                in_background = False
                continue

            # Scenario
            match = self.SCENARIO_RE.match(line)
            if match:
                current_scenario = GherkinScenario(
                    name=match.group(1).strip(), line=i
                )
                feature.scenarios.append(current_scenario)
                in_background = False
                continue

            # Steps (Given/When/Then/And/But)
            match = self.STEP_RE.match(line)
            if match and current_scenario is not None:
                keyword = match.group(1).capitalize()
                # Normalizar: "given" → "Given", etc.
                if keyword in ("Given", "When", "Then", "And", "But"):
                    step = GherkinStep(
                        keyword=keyword,
                        text=match.group(2).strip(),
                        line=i,
                    )
                    current_scenario.steps.append(step)
                continue

            # Examples: ignorar (es metadata de Scenario Outline)
            if self.EXAMPLES_RE.match(line):
                continue

        return feature

    def parse_file(self, file_path) -> Optional[GherkinFeature]:
        """
        Parsea un archivo .feature desde disco.

        Args:
            file_path: Ruta al archivo .feature

        Returns:
            GherkinFeature o None si no se puede leer/parsear
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self.parse(content)
        except Exception as e:
            logger.debug("Error parsing gherkin file %s: %s", file_path, e)
            return None
