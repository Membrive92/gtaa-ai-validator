"""
Generador de reportes en formato JSON.

Exporta los resultados de análisis a un fichero JSON estructurado
con metadatos, resumen y lista detallada de violaciones.
"""

import json
from pathlib import Path

from gtaa_validator.models import Report


class JsonReporter:
    """Genera reportes de análisis en formato JSON."""

    def generate(self, report: Report, output_path: Path) -> None:
        """
        Generar reporte JSON y escribirlo al fichero indicado.

        Args:
            report: Resultado del análisis estático
            output_path: Ruta del fichero JSON de salida
        """
        data = report.to_dict()
        output_path = Path(output_path)
        output_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
