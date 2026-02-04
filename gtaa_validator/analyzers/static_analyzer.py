"""
Analizador Estático para gTAA Validator.

Este módulo orquesta el análisis estático de proyectos de test automation.
Coordina múltiples checkers, agrega resultados y produce un Report.

El StaticAnalyzer implementa el Patrón Facade: proporciona una interfaz simple
(método analyze()) a un subsistema complejo de checkers.

Responsabilidades principales:
- Descubrir archivos en el proyecto (Python, Java, JS/TS, C#, Gherkin)
- Ejecutar los checkers apropiados en cada archivo
- Agregar violaciones de todos los checkers
- Calcular la puntuación de cumplimiento
- Generar el Report final

Fase 9+: Los checkers son ahora agnósticos al lenguaje usando ParseResult.
Los mismos checkers funcionan para Python, Java, JavaScript/TypeScript y C#.

Uso:
    analyzer = StaticAnalyzer(project_path)
    report = analyzer.analyze()
    print(f"Puntuación: {report.score}")
"""

import fnmatch
import time
from pathlib import Path
from typing import List, Optional

from gtaa_validator.models import Report, Violation
from gtaa_validator.checkers.base import BaseChecker
from gtaa_validator.checkers.definition_checker import DefinitionChecker
from gtaa_validator.checkers.structure_checker import StructureChecker
from gtaa_validator.checkers.adaptation_checker import AdaptationChecker
from gtaa_validator.checkers.quality_checker import QualityChecker
from gtaa_validator.checkers.bdd_checker import BDDChecker
from gtaa_validator.file_classifier import FileClassifier
from gtaa_validator.config import ProjectConfig, load_config
from gtaa_validator.parsers.treesitter_base import ParseResult, get_parser_for_file


class StaticAnalyzer:
    """
    Orquesta el análisis estático de un proyecto de test automation.

    El analizador:
    1. Descubre todos los archivos Python del proyecto
    2. Filtra archivos según las capacidades de cada checker
    3. Ejecuta cada checker sobre los archivos aplicables
    4. Agrega todas las violaciones
    5. Calcula la puntuación de cumplimiento
    6. Devuelve un Report completo

    Atributos:
        project_path: Directorio raíz del proyecto a analizar
        checkers: Lista de instancias de checkers a ejecutar
        verbose: Si se debe imprimir información detallada del progreso
    """

    def __init__(self, project_path: Path, verbose: bool = False,
                 config: Optional[ProjectConfig] = None):
        """
        Inicializar el StaticAnalyzer.

        Args:
            project_path: Ruta al directorio raíz del proyecto
            verbose: Si es True, imprimir progreso detallado del análisis
            config: Configuración del proyecto (si None, se carga de .gtaa.yaml)
        """
        self.project_path = Path(project_path).resolve()
        self.verbose = verbose
        self.config = config if config is not None else load_config(self.project_path)
        self.classifier = FileClassifier()
        self.checkers: List[BaseChecker] = self._initialize_checkers()

    def _initialize_checkers(self) -> List[BaseChecker]:
        """
        Inicializar todos los checkers disponibles.

        Fase 9+: Los checkers son agnósticos al lenguaje.
        Funcionan con Python, Java, JavaScript/TypeScript y C#.

        Returns:
            Lista de instancias de checkers inicializados
        """
        checkers = [
            DefinitionChecker(),   # ADAPTATION_IN_DEFINITION (all langs)
            StructureChecker(),    # Directory structure (Python only)
            AdaptationChecker(),   # Page Object violations (all langs)
            QualityChecker(),      # Quality issues (all langs)
            BDDChecker(),          # BDD/Gherkin (Python + .feature)
        ]

        if self.verbose:
            checker_names = [c.name for c in checkers]
            print(f"Inicializados {len(checkers)} checkers: {', '.join(checker_names)}")

        return checkers

    def analyze(self) -> Report:
        """
        Realizar el análisis estático completo del proyecto.

        Este es el punto de entrada principal para el análisis estático.
        Orquesta todo el proceso de verificación y devuelve un Report.

        Returns:
            Objeto Report conteniendo todas las violaciones y metadatos

        Ejemplo:
            analyzer = StaticAnalyzer(Path("./mi-proyecto"))
            report = analyzer.analyze()
            print(f"Encontradas {len(report.violations)} violaciones")
            print(f"Puntuación: {report.score}/100")
        """
        start_time = time.time()

        if self.verbose:
            print(f"\nIniciando análisis estático de: {self.project_path}")
            print("="*60)

        # Inicializar informe
        report = Report(
            project_path=self.project_path,
            violations=[],
            files_analyzed=0
        )

        # Ejecutar verificaciones a nivel de proyecto (ej. estructura de directorios)
        for checker in self.checkers:
            try:
                project_violations = checker.check_project(self.project_path)
                if project_violations:
                    report.violations.extend(project_violations)
                    if self.verbose:
                        print(f"  [{checker.name}] Encontrada(s) {len(project_violations)} violación(es) a nivel de proyecto")
            except Exception as e:
                if self.verbose:
                    print(f"  [{checker.name}] Error en verificación de proyecto: {str(e)}")

        # Descubrir todos los archivos Python
        python_files = self._discover_python_files()

        if self.verbose:
            py_count = sum(1 for f in python_files if f.suffix == ".py")
            feature_count = sum(1 for f in python_files if f.suffix == ".feature")
            extra = f" + {feature_count} .feature" if feature_count else ""
            print(f"\nEncontrados {py_count} archivos Python{extra}")

        # Analizar cada archivo con los checkers aplicables
        for file_path in python_files:
            if self.verbose:
                relative_path = self._get_relative_path(file_path)
                print(f"  Verificando: {relative_path}")

            file_violations = self._check_file(file_path)
            report.violations.extend(file_violations)
            report.files_analyzed += 1

        # Calcular puntuación basada en violaciones
        report.calculate_score()

        # Registrar tiempo de ejecución
        report.execution_time_seconds = time.time() - start_time

        if self.verbose:
            print("\n" + "="*60)
            print("¡Análisis completado!")
            print(f"Archivos analizados: {report.files_analyzed}")
            print(f"Violaciones encontradas: {len(report.violations)}")
            print(f"Puntuación: {report.score:.1f}/100")
            print(f"Tiempo: {report.execution_time_seconds:.2f}s")

        return report

    def _discover_python_files(self) -> List[Path]:
        """
        Descubrir todos los archivos analizables en el proyecto.

        Busca archivos de código fuente soportados, excluyendo directorios
        comunes que no deben analizarse (venv, .git, node_modules, etc.)

        Returns:
            Lista de objetos Path para todos los archivos encontrados
        """
        # Directorios a excluir del análisis
        exclude_dirs = {
            "venv", "env", "ENV", ".venv",  # Entornos virtuales
            ".git", ".hg", ".svn",           # Control de versiones
            "__pycache__",                    # Caché de Python
            "node_modules",                   # Dependencias de JavaScript
            ".pytest_cache", ".tox",         # Artefactos de testing
            "build", "dist", "*.egg-info",   # Artefactos de build
            "bin", "obj",                     # Artefactos de C#
            "target",                         # Artefactos de Java/Maven
        }

        # Extensiones a buscar (Fase 9: multi-lang)
        extensions = (
            "*.py",                           # Python
            "*.feature",                      # Gherkin/BDD
            "*.java",                         # Java
            "*.js", "*.ts", "*.jsx", "*.tsx", # JavaScript/TypeScript
            "*.mjs", "*.cjs",                 # ES modules
            "*.cs",                           # C#
        )

        found_files = []

        for ext in extensions:
            for file_path in self.project_path.rglob(ext):
                # Verificar si el archivo está en un directorio excluido
                should_exclude = any(
                    excluded in file_path.parts
                    for excluded in exclude_dirs
                )

                if not should_exclude:
                    # Filtrar por ignore_paths de la configuración
                    relative_str = str(file_path.relative_to(self.project_path)).replace("\\", "/")
                    ignored = any(
                        fnmatch.fnmatch(relative_str, pattern)
                        for pattern in self.config.ignore_paths
                    )
                    if not ignored:
                        found_files.append(file_path)

        # Ordenar para un orden consistente
        found_files.sort()

        return found_files

    def _check_file(self, file_path: Path) -> List[Violation]:
        """
        Ejecutar todos los checkers aplicables sobre un único archivo.

        Parsea el archivo una sola vez usando el parser apropiado y pasa
        el ParseResult a todos los checkers, evitando parseo redundante.

        Fase 9+: Usa ParseResult unificado para todos los lenguajes.

        Args:
            file_path: Ruta al archivo a verificar

        Returns:
            Lista de todas las violaciones encontradas por todos los checkers
        """
        violations = []

        # Determinar qué checkers aplican a este archivo
        applicable = [c for c in self.checkers if c.can_check(file_path)]
        if not applicable:
            return violations

        # Parsear archivo una sola vez usando el parser apropiado
        parse_result: Optional[ParseResult] = None
        source_code = ""
        file_type = "unknown"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            # Obtener parser apropiado para el lenguaje
            parser = get_parser_for_file(file_path)
            if parser:
                parse_result = parser.parse(source_code)

            # Clasificar archivo (funciona con ParseResult o AST legacy)
            if parse_result is not None:
                classification = self.classifier.classify_detailed(
                    file_path, source_code, parse_result
                )
                file_type = classification.file_type

                if self.verbose and file_type != "unknown":
                    relative = self._get_relative_path(file_path)
                    fw_info = f" (frameworks: {', '.join(classification.frameworks)})" if classification.frameworks else ""
                    bdd_info = " [BDD]" if classification.is_bdd else ""
                    print(f"    [Clasificación] {relative} → {file_type}{fw_info}{bdd_info}")

        except (SyntaxError, Exception):
            # Si el parseo falla, dejar que los checkers individuales lo manejen
            pass

        for checker in applicable:
            try:
                # Pasar ParseResult a los checkers (soportan tanto ParseResult como AST legacy)
                checker_violations = checker.check(file_path, parse_result, file_type=file_type)
                violations.extend(checker_violations)

                if self.verbose and checker_violations:
                    print(f"    [{checker.name}] Encontrada(s) {len(checker_violations)} violación(es)")

            except Exception as e:
                # No fallar si un checker individual falla
                if self.verbose:
                    print(f"    [{checker.name}] Error: {str(e)}")

        return violations

    def _get_relative_path(self, file_path: Path) -> Path:
        """
        Obtener la ruta relativa al directorio raíz del proyecto.

        Args:
            file_path: Ruta absoluta al archivo

        Returns:
            Ruta relativa al directorio raíz del proyecto
        """
        try:
            return file_path.relative_to(self.project_path)
        except ValueError:
            return file_path

    def get_summary(self) -> dict:
        """
        Obtener un resumen de la configuración del analizador.

        Returns:
            Diccionario con información del analizador
        """
        return {
            "project_path": str(self.project_path),
            "checker_count": len(self.checkers),
            "checkers": [c.name for c in self.checkers],
        }
