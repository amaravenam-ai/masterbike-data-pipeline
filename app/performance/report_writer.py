import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"
PERFORMANCE_JSON = REPORTS_DIR / "performance_report.json"
PERFORMANCE_MD = REPORTS_DIR / "performance_report.md"


def write_performance_report(report: Dict[str, Any]) -> Dict[str, str]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_files = {
        "json": str(PERFORMANCE_JSON),
        "markdown": str(PERFORMANCE_MD),
    }
    report["report_files"] = report_files

    with PERFORMANCE_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    PERFORMANCE_MD.write_text(_to_markdown(report), encoding="utf-8")

    return report_files


def read_performance_report() -> Dict[str, Any]:
    if not PERFORMANCE_JSON.exists():
        return {
            "status": "NOT_FOUND",
            "message": "No existe reporte de rendimiento. Ejecuta /api/performance/run primero.",
            "report_path": str(PERFORMANCE_JSON),
        }

    with PERFORMANCE_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def _to_markdown(report: Dict[str, Any]) -> str:
    generated_at = report.get("generated_at") or datetime.utcnow().isoformat()
    slowest = report.get("slowest_stage") or {}

    lines = [
        "# Reporte simple de rendimiento",
        "",
        f"- Generado: {generated_at}",
        f"- Estado: {report.get('status', 'N/A')}",
        f"- Tiempo total: {report.get('execution_time_seconds', 0)} segundos",
        f"- CPU aproximada: {report.get('cpu_percent', 0)}%",
        f"- Memoria aproximada: {report.get('memory_mb', 0)} MB",
        f"- Registros procesados: {report.get('total_records', 0)}",
        f"- Registros validos: {report.get('valid_records', 0)}",
        f"- Registros con error: {report.get('error_records', 0)}",
        "",
        "## Etapa mas lenta",
        "",
        f"- Fuente: {slowest.get('source', 'N/A')}",
        f"- Etapa: {slowest.get('stage', 'N/A')}",
        f"- Duracion: {slowest.get('duration_ms', 0)} ms",
        "",
        "## Recomendacion",
        "",
        report.get("recommendation", "Sin recomendacion disponible."),
        "",
    ]
    return "\n".join(lines)
