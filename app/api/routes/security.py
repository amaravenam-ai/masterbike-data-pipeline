from fastapi import APIRouter

from app.security.report_writer import read_security_report
from app.security.security_auditor import SecurityAuditor


router = APIRouter(prefix="/api/security", tags=["Security"])


@router.get("/audit", summary="Ejecutar auditoria simple de seguridad")
def run_security_audit():
    """Ejecuta una auditoria estatica simple del proyecto y genera reportes."""
    return SecurityAuditor().run()


@router.get("/report", summary="Obtener ultimo reporte de seguridad")
def get_security_report():
    """Retorna el ultimo reporte JSON generado por /api/security/audit."""
    return read_security_report()
