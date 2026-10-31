import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from app.security.report_writer import write_security_report


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SENSITIVE_KEYS = {
    "email",
    "correo",
    "telefono",
    "teléfono",
    "phone",
    "nombre",
    "direccion",
    "dirección",
    "id_usuario",
    "user_id",
}
SECRET_PATTERN = re.compile(
    r"(?i)\b(password|passwd|pwd|token|secret|api_key|database_url|postgres_password)\b\s*[:=]\s*(.+)"
)
URL_WITH_CREDENTIALS_PATTERN = re.compile(r"postgresql://[^:\s]+:[^@\s]+@")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SecurityAuditor:
    """Performs a simple static security audit for the project."""

    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.project_root = project_root
        self.findings: List[Dict[str, Any]] = []

    def run(self) -> Dict[str, Any]:
        self.findings = []
        self._audit_env_files()
        self._audit_docker_compose()
        self._scan_possible_secrets()
        self._audit_logs()
        self._audit_mock_sensitive_data()

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_findings": len(self.findings),
            "high_risk": self._count_risk("alto"),
            "medium_risk": self._count_risk("medio"),
            "low_risk": self._count_risk("bajo"),
            "findings": self.findings,
            "recommendations": self._build_recommendations(),
        }
        report["report_files"] = write_security_report(report)
        return report

    def _audit_env_files(self) -> None:
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"

        if not env_file.exists():
            self._add_finding(
                risk="bajo",
                category="configuracion",
                title="Archivo .env no encontrado",
                file=".env",
                evidence="No existe .env en el entorno local del proyecto.",
                recommendation="Mantener credenciales reales en .env local y no subirlo a repositorios.",
            )

        if not env_example.exists():
            self._add_finding(
                risk="bajo",
                category="configuracion",
                title="Archivo .env.example no encontrado",
                file=".env.example",
                evidence="No existe plantilla de variables de entorno.",
                recommendation="Agregar .env.example sin secretos reales para documentar configuracion requerida.",
            )

    def _audit_docker_compose(self) -> None:
        compose = self.project_root / "docker-compose.yml"
        if not compose.exists():
            self._add_finding(
                risk="bajo",
                category="docker",
                title="docker-compose.yml no encontrado",
                file="docker-compose.yml",
                evidence="No existe archivo docker-compose.yml.",
                recommendation="Mantener docker-compose.yml versionado para reproducir el entorno.",
            )
            return

        lines = compose.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, line in enumerate(lines, start=1):
            lower = line.lower()
            if "postgres_password" in lower or "database_url" in lower:
                self._add_finding(
                    risk="medio",
                    category="credenciales",
                    title="Credencial visible en docker-compose.yml",
                    file="docker-compose.yml",
                    line=idx,
                    evidence=self._mask_line(line.strip()),
                    recommendation="Mover credenciales a variables de entorno y mantener .env fuera de Git.",
                )

            if re.search(r'["\']?\d+:\d+["\']?', line):
                risk = "medio" if "5432" in line else "bajo"
                title = "Puerto PostgreSQL expuesto" if "5432" in line else "Puerto de aplicacion expuesto"
                self._add_finding(
                    risk=risk,
                    category="docker",
                    title=title,
                    file="docker-compose.yml",
                    line=idx,
                    evidence=line.strip(),
                    recommendation="Limitar puertos expuestos segun el entorno y usar redes internas cuando sea posible.",
                )

    def _scan_possible_secrets(self) -> None:
        allowed_extensions = {".py", ".yml", ".yaml", ".env", ".example", ".md", ".txt"}
        ignored_parts = {".git", "__pycache__", "reports", "venv", ".venv", "node_modules", "security"}
        seen = set()

        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in ignored_parts for part in path.parts):
                continue
            if path.suffix.lower() not in allowed_extensions and path.name != ".env.example":
                continue

            rel = path.relative_to(self.project_root).as_posix()
            if rel == "docker-compose.yml":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for idx, line in enumerate(text.splitlines(), start=1):
                assignment = SECRET_PATTERN.search(line)
                has_url_secret = URL_WITH_CREDENTIALS_PATTERN.search(line)
                if not assignment and not has_url_secret:
                    continue
                if assignment and self._looks_like_reference_only(assignment.group(2)):
                    continue
                key = (rel, idx, line.strip().lower())
                if key in seen:
                    continue
                seen.add(key)
                self._add_finding(
                    risk="medio",
                    category="secretos",
                    title="Posible secreto o credencial en archivo",
                    file=rel,
                    line=idx,
                    evidence=self._mask_line(line.strip()),
                    recommendation="Revisar el valor y mover secretos reales a .env o gestor de secretos.",
                )

    def _audit_logs(self) -> None:
        logs_dir = self.project_root / "app" / "logs"
        if not logs_dir.exists():
            return

        for path in logs_dir.rglob("*.log"):
            rel = path.relative_to(self.project_root).as_posix()
            for idx, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
                lower = line.lower()
                if "critical" in lower or "fatal" in lower or "traceback" in lower:
                    self._add_finding(
                        risk="alto",
                        category="logs",
                        title="Error critico encontrado en logs",
                        file=rel,
                        line=idx,
                        evidence=self._truncate(line.strip()),
                        recommendation="Revisar logs criticos y corregir la causa antes de publicar el pipeline.",
                    )
                elif "error" in lower:
                    self._add_finding(
                        risk="medio",
                        category="logs",
                        title="Error encontrado en logs",
                        file=rel,
                        line=idx,
                        evidence=self._truncate(line.strip()),
                        recommendation="Revisar errores periodicamente y definir alertas para fallas repetidas.",
                    )

    def _audit_mock_sensitive_data(self) -> None:
        mock_dir = self.project_root / "mock_data"
        if not mock_dir.exists():
            return

        for path in mock_dir.glob("*.json"):
            data = self._read_json(path)
            counters = self._count_sensitive_items(data)
            if not counters:
                continue

            self._add_finding(
                risk="medio",
                category="datos_sensibles",
                title="Datos personales presentes en mock_data",
                file=path.relative_to(self.project_root).as_posix(),
                evidence=", ".join(f"{key}: {value}" for key, value in sorted(counters.items())),
                recommendation="Enmascarar o anonimizar datos personales en ambientes de demo y pruebas.",
            )

    def _count_sensitive_items(self, data: Any) -> Dict[str, int]:
        counters: Dict[str, int] = {}
        for item in self._walk_json(data):
            if not isinstance(item, tuple):
                continue
            key, value = item
            normalized_key = str(key).lower()
            if normalized_key in SENSITIVE_KEYS:
                counters[normalized_key] = counters.get(normalized_key, 0) + 1
            elif isinstance(value, str) and EMAIL_PATTERN.match(value.strip()):
                counters["email_value"] = counters.get("email_value", 0) + 1
        return counters

    def _walk_json(self, data: Any) -> Iterable[Any]:
        if isinstance(data, dict):
            for key, value in data.items():
                yield key, value
                yield from self._walk_json(value)
        elif isinstance(data, list):
            for item in data:
                yield from self._walk_json(item)

    def _read_json(self, path: Path) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def _mask_line(self, line: str) -> str:
        line = re.sub(
            r"(?i)(password\s*[:=]\s*)([^\s]+)",
            lambda m: m.group(1) + self._mask_secret(m.group(2)),
            line,
        )
        line = re.sub(
            r"(?i)(postgres_password\s*[:=]\s*)([^\s]+)",
            lambda m: m.group(1) + self._mask_secret(m.group(2)),
            line,
        )
        line = re.sub(
            r"(postgresql://[^:\s]+:)([^@\s]+)(@)",
            lambda m: m.group(1) + self._mask_secret(m.group(2)) + m.group(3),
            line,
        )
        return self._truncate(line)

    def _mask_secret(self, value: str) -> str:
        clean = value.strip().strip('"').strip("'")
        if len(clean) <= 2:
            return "*" * len(clean)
        return clean[:2] + ("*" * (len(clean) - 2))

    def _looks_like_reference_only(self, value: str) -> bool:
        clean = value.strip().strip('"').strip("'")
        if not clean:
            return True
        reference_markers = ("os.getenv(", "none", "null", "true", "false")
        return clean.lower().startswith(reference_markers)

    def _truncate(self, value: str, max_length: int = 180) -> str:
        return value if len(value) <= max_length else value[: max_length - 3] + "..."

    def _add_finding(
        self,
        risk: str,
        category: str,
        title: str,
        file: str,
        evidence: str,
        recommendation: str,
        line: int | None = None,
    ) -> None:
        finding = {
            "risk": risk,
            "category": category,
            "title": title,
            "file": file,
            "evidence": evidence,
            "recommendation": recommendation,
        }
        if line is not None:
            finding["line"] = line
        self.findings.append(finding)

    def _count_risk(self, risk: str) -> int:
        return sum(1 for finding in self.findings if finding.get("risk") == risk)

    def _build_recommendations(self) -> List[str]:
        recommendations = [
            "Mover credenciales a .env y no subir .env a GitHub.",
            "Limitar puertos expuestos, especialmente PostgreSQL, en ambientes no locales.",
            "Usar roles con minimos privilegios para base de datos y API.",
            "Enmascarar datos sensibles en mock_data cuando se usen para demos.",
            "Revisar logs periodicamente y atender errores criticos.",
        ]
        return recommendations
