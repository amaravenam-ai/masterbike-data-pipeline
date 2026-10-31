import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"
SECURITY_JSON = REPORTS_DIR / "security_audit.json"
SECURITY_MD = REPORTS_DIR / "security_audit.md"


def write_security_report(report: Dict[str, Any]) -> Dict[str, str]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_files = {
        "json": str(SECURITY_JSON),
        "markdown": str(SECURITY_MD),
    }
    report["report_files"] = report_files

    with SECURITY_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    SECURITY_MD.write_text(_to_markdown(report), encoding="utf-8")

    return report_files


def read_security_report() -> Dict[str, Any]:
    if not SECURITY_JSON.exists():
        return {
            "status": "NOT_FOUND",
            "message": "No existe reporte de seguridad. Ejecuta /api/security/audit primero.",
            "report_path": str(SECURITY_JSON),
        }

    with SECURITY_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def _to_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# Auditoria simple de seguridad",
        "",
        f"- Generado: {report.get('generated_at') or datetime.utcnow().isoformat()}",
        f"- Hallazgos totales: {report.get('total_findings', 0)}",
        f"- Riesgo alto: {report.get('high_risk', 0)}",
        f"- Riesgo medio: {report.get('medium_risk', 0)}",
        f"- Riesgo bajo: {report.get('low_risk', 0)}",
        "",
        "## Hallazgos",
        "",
    ]

    for finding in report.get("findings", []):
        lines.extend([
            f"### {finding.get('title', 'Hallazgo')}",
            "",
            f"- Riesgo: {finding.get('risk', 'N/A')}",
            f"- Categoria: {finding.get('category', 'N/A')}",
            f"- Archivo: {finding.get('file', 'N/A')}",
            f"- Evidencia: {finding.get('evidence', 'N/A')}",
            f"- Recomendacion: {finding.get('recommendation', 'N/A')}",
            "",
        ])

    lines.extend(["## Recomendaciones generales", ""])
    for item in report.get("recommendations", []):
        lines.append(f"- {item}")

    lines.append("")
    return "\n".join(lines)
