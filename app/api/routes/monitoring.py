from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db, check_db_connection
from app.monitoring.metrics import get_recent_logs, get_all_metrics

router = APIRouter(prefix="/monitoring", tags=["Monitoreo y Observabilidad"])


# @Operation (OpenAPI): Verifica el estado del sistema y conectividad con PostgreSQL.
# @ApiResponses (OpenAPI): Documenta respuesta 200 con estado healthy o degraded.
# @Content + @ExampleObject: Ejemplo concreto del JSON de respuesta en Swagger UI.
@router.get(
    "/health",
    summary="Health check del sistema",
    responses={
        200: {
            "description": "Estado del sistema obtenido correctamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "database": "connected",
                        "timestamp": "2026-06-02T12:00:00",
                        "version": "1.0.0",
                        "componentes": {
                            "fastapi": "ok",
                            "postgresql": "ok",
                            "ingestion": "ok",
                            "validation": "ok",
                            "transformation": "ok",
                        },
                    }
                }
            },
        }
    },
)
def health_check(db: Session = Depends(get_db)):
    """Verifica el estado del sistema y la conectividad con PostgreSQL."""
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "componentes": {
            "fastapi": "ok",
            "postgresql": "ok" if db_ok else "error",
            "ingestion": "ok",
            "validation": "ok",
            "transformation": "ok",
        },
    }


# @Operation (OpenAPI): Retorna métricas agregadas de todas las ejecuciones del pipeline.
# @ApiResponses (OpenAPI): Documenta respuesta 200 con métricas globales acumuladas por fuente.
# @Content + @ExampleObject: Ejemplo del JSON de métricas en Swagger UI.
@router.get(
    "/metrics",
    summary="Métricas globales del pipeline",
    responses={
        200: {
            "description": "Métricas globales agregadas de todas las fuentes",
            "content": {
                "application/json": {
                    "example": {
                        "ventas": {"total_runs": 3, "total_registros": 45, "tasa_calidad": 66.67},
                        "usuarios": {"total_runs": 2, "total_registros": 26, "tasa_calidad": 69.23},
                    }
                }
            },
        }
    },
)
def get_metrics():
    """Retorna métricas agregadas de todas las ejecuciones del pipeline."""
    return get_all_metrics()


# @Operation (OpenAPI): Retorna logs recientes del pipeline con trazabilidad completa.
# @ApiResponses (OpenAPI): Documenta respuesta 200 con lista de logs filtrable por fuente.
# @Parameter (OpenAPI): limit y fuente son parámetros de query con descripción y ejemplo.
# @Content + @ExampleObject: Ejemplo de la estructura de logs retornados.
@router.get(
    "/logs",
    summary="Logs recientes del pipeline",
    responses={
        200: {
            "description": "Logs recientes del pipeline con trazabilidad",
            "content": {
                "application/json": {
                    "example": {
                        "total": 2,
                        "fuente_filtro": "ventas",
                        "logs": [
                            {
                                "run_id": "550e8400-e29b-41d4-a716-446655440000",
                                "fuente": "ventas",
                                "stage": "validation",
                                "event_type": "VALIDATION_COMPLETE",
                                "mensaje": "10 válidos, 5 errores",
                                "timestamp": "2026-06-02T12:00:00",
                            }
                        ],
                    }
                }
            },
        }
    },
)
def get_logs(
    # @Parameter (OpenAPI): Límite de logs a retornar. Máximo 500.
    limit: int = Query(100, ge=1, le=500, description="Número máximo de logs a retornar"),
    # @Parameter (OpenAPI): Filtra los logs por nombre de fuente de datos.
    fuente: Optional[str] = Query(None, description="Filtrar logs por fuente de datos", example="ventas"),
):
    """
    Retorna los logs más recientes del pipeline con trazabilidad completa.

    Incluye: run_id, fuente, stage, event_type, mensaje, timestamp.
    """
    logs = get_recent_logs(limit=limit, fuente=fuente)
    return {
        "total": len(logs),
        "fuente_filtro": fuente,
        "logs": logs,
    }


# @Operation (OpenAPI): Calcula estadísticas de calidad de datos por fuente desde PostgreSQL.
# @ApiResponses (OpenAPI): Documenta respuesta 200 con estadísticas y tasa de calidad por fuente.
# @Content + @ExampleObject: Ejemplo con conteos de registros y promedio de duración.
@router.get(
    "/stats",
    summary="Estadísticas por fuente desde la base de datos",
    responses={
        200: {
            "description": "Estadísticas de calidad de datos por fuente",
            "content": {
                "application/json": {
                    "example": {
                        "fuentes": {
                            "ventas": {
                                "total_runs": 3,
                                "total_registros": 45,
                                "total_validos": 30,
                                "total_errores": 15,
                                "tasa_calidad": 66.67,
                                "promedio_duracion_segundos": 1.23,
                            }
                        },
                        "timestamp": "2026-06-02T12:00:00",
                    }
                }
            },
        }
    },
)
def get_stats_from_db(db: Session = Depends(get_db)):
    """Calcula estadísticas de calidad de datos por fuente desde PostgreSQL."""
    from app.models.pipeline_models import PipelineRun

    fuentes = ["ventas", "usuarios", "inventario", "arriendos", "bicicletas", "despachos"]
    stats = {}

    for fuente in fuentes:
        runs = (
            db.query(PipelineRun)
            .filter(PipelineRun.fuente == fuente)
            .filter(PipelineRun.estado == "COMPLETED")
            .all()
        )
        if not runs:
            stats[fuente] = {
                "total_runs": 0,
                "total_registros": 0,
                "total_validos": 0,
                "total_errores": 0,
                "tasa_calidad": 0,
                "promedio_duracion_segundos": 0,
            }
            continue

        total_reg = sum(r.total_registros or 0 for r in runs)
        total_val = sum(r.registros_validos or 0 for r in runs)
        total_err = sum(r.registros_error or 0 for r in runs)
        duraciones = [float(r.duracion_segundos) for r in runs if r.duracion_segundos]

        stats[fuente] = {
            "total_runs": len(runs),
            "total_registros": total_reg,
            "total_validos": total_val,
            "total_errores": total_err,
            "tasa_calidad": round(total_val / total_reg * 100, 2) if total_reg > 0 else 0,
            "promedio_duracion_segundos": round(sum(duraciones) / len(duraciones), 3) if duraciones else 0,
        }

    return {
        "fuentes": stats,
        "timestamp": datetime.utcnow().isoformat(),
    }
