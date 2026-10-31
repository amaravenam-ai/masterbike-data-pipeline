from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.performance.performance_analyzer import PerformanceAnalyzer
from app.performance.report_writer import read_performance_report


router = APIRouter(prefix="/api/performance", tags=["Performance"])


@router.get("/run", summary="Ejecutar analisis simple de rendimiento")
def run_performance_analysis(
    source: str = Query("all", description="Fuente a medir: all, ventas, usuarios, inventario, arriendos, bicicletas, despachos"),
    db: Session = Depends(get_db),
):
    """
    Ejecuta el pipeline existente y genera un reporte simple de rendimiento.
    """
    try:
        return PerformanceAnalyzer(db).run(source=source)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/report", summary="Obtener ultimo reporte de rendimiento")
def get_performance_report():
    """Retorna el ultimo reporte JSON generado por /api/performance/run."""
    return read_performance_report()
