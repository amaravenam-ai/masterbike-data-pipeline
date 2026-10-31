import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.ingestion import SOURCES
from app.pipeline.loader import LoaderStage

router = APIRouter(prefix="/pipeline", tags=["Pipeline ETL"])


# @Operation (OpenAPI): Ejecuta el pipeline ETL completo para una fuente específica.
# @ApiResponses (OpenAPI): Documenta los códigos de respuesta posibles del endpoint.
#   - 200: pipeline ejecutado con éxito, incluye métricas de la ejecución.
#   - 400: la fuente indicada no existe en el sistema.
# @Content + @ExampleObject: Ejemplos concretos de JSON en Swagger UI por cada respuesta.
@router.post(
    "/run/{source}",
    response_model=dict,
    summary="Ejecutar pipeline para una fuente",
    responses={
        200: {
            "description": "Pipeline ejecutado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "fuente": "ventas",
                        "estado": "COMPLETED",
                        "total_registros": 15,
                        "registros_validos": 10,
                        "registros_error": 5,
                        "duracion_segundos": 1.23,
                    }
                }
            },
        },
        400: {
            "description": "Fuente no válida",
            "content": {
                "application/json": {
                    "example": {"detail": "Fuente 'xyz' no válida. Fuentes disponibles: ['ventas', 'usuarios', ...]"}
                }
            },
        },
    },
)
def run_pipeline(
    # @Parameter (OpenAPI): Nombre de la fuente de datos a procesar. Debe ser una fuente registrada.
    source: str = Path(..., description="Nombre de la fuente de datos a procesar", example="ventas"),
    db: Session = Depends(get_db),
):
    """
    Ejecuta el pipeline ETL completo para la fuente indicada.

    **Flujo:** Ingesta → Validación → Transformación → Carga PostgreSQL

    **Fuentes disponibles:** ventas, usuarios, inventario, arriendos, bicicletas, despachos
    """
    if source not in SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Fuente '{source}' no válida. Fuentes disponibles: {SOURCES}",
        )

    orchestrator = PipelineOrchestrator(db)
    result = orchestrator.run(source)
    if result.estado != "COMPLETED":
        raise HTTPException(status_code=500, detail=result.to_dict())
    return result.to_dict()


# @Operation (OpenAPI): Ejecuta el pipeline ETL para todas las fuentes de forma secuencial.
# @ApiResponses (OpenAPI): Documenta respuesta 200 con el resumen consolidado de todas las fuentes.
# @Content + @ExampleObject: Ejemplo del JSON de respuesta con totales acumulados.
@router.post(
    "/run-all",
    response_model=dict,
    summary="Ejecutar todos los pipelines",
    responses={
        200: {
            "description": "Todos los pipelines ejecutados exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "total_fuentes": 6,
                        "total_registros": 75,
                        "total_validos": 57,
                        "total_errores": 18,
                        "duracion_total_segundos": 4.56,
                    }
                }
            },
        }
    },
)
def run_all_pipelines(db: Session = Depends(get_db)):
    """
    Ejecuta el pipeline ETL para todas las fuentes de MasterBike secuencialmente.
    """
    orchestrator = PipelineOrchestrator(db)
    start = time.time()
    resultados = []
    total_registros = 0
    total_validos = 0
    total_errores = 0

    for source in SOURCES:
        result = orchestrator.run(source)
        resultados.append(result.to_dict())
        total_registros += result.total_registros
        total_validos += result.registros_validos
        total_errores += result.registros_error

    duracion_total = round(time.time() - start, 3)

    payload = {
        "estado": "COMPLETED" if all(r["estado"] == "COMPLETED" for r in resultados) else "FAILED",
        "total_fuentes": len(SOURCES),
        "resultados": resultados,
        "total_registros": total_registros,
        "total_validos": total_validos,
        "total_errores": total_errores,
        "duracion_total_segundos": duracion_total,
    }
    if payload["estado"] != "COMPLETED":
        raise HTTPException(status_code=500, detail=payload)
    return payload


# @Operation (OpenAPI): Lista el historial de ejecuciones del pipeline con métricas.
# @ApiResponses (OpenAPI): Documenta respuesta 200 con lista paginada de ejecuciones.
# @Parameter (OpenAPI): source, limit y offset son parámetros de query opcionales documentados.
@router.get(
    "/runs",
    summary="Listar ejecuciones del pipeline",
    responses={
        200: {
            "description": "Lista paginada de ejecuciones del pipeline",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "fuente": "ventas",
                            "estado": "COMPLETED",
                            "total_registros": 15,
                            "registros_validos": 10,
                            "registros_error": 5,
                            "duracion_segundos": 1.23,
                            "tasa_exito": 66.67,
                        }
                    ]
                }
            },
        }
    },
)
def list_runs(
    # @Parameter (OpenAPI): Filtra el historial por fuente de datos específica.
    source: Optional[str] = Query(None, description="Filtrar historial por fuente de datos", example="ventas"),
    # @Parameter (OpenAPI): Número máximo de ejecuciones a retornar.
    limit: int = Query(50, ge=1, le=200, description="Número máximo de ejecuciones a retornar"),
    # @Parameter (OpenAPI): Número de registros a omitir para paginación.
    offset: int = Query(0, ge=0, description="Número de registros a omitir para paginación"),
    db: Session = Depends(get_db),
):
    """Retorna el historial de ejecuciones del pipeline con métricas."""
    loader = LoaderStage(db)
    runs = loader.list_runs(source=source, limit=limit, offset=offset)
    return [
        {
            "id": str(r.id),
            "fuente": r.fuente,
            "estado": r.estado,
            "fecha_inicio": r.fecha_inicio.isoformat() if r.fecha_inicio else None,
            "fecha_fin": r.fecha_fin.isoformat() if r.fecha_fin else None,
            "total_registros": r.total_registros,
            "registros_validos": r.registros_validos,
            "registros_error": r.registros_error,
            "duracion_segundos": float(r.duracion_segundos) if r.duracion_segundos else None,
            "tasa_exito": round(r.registros_validos / r.total_registros * 100, 2) if r.total_registros > 0 else 0,
        }
        for r in runs
    ]


# @Operation (OpenAPI): Obtiene el detalle completo de una ejecución por su UUID.
# @ApiResponses (OpenAPI): Documenta tres posibles respuestas:
#   - 200: ejecución encontrada con todos sus datos.
#   - 400: el run_id proporcionado no tiene formato UUID válido.
#   - 404: no existe ninguna ejecución con ese ID.
# @Parameter (OpenAPI): run_id es el identificador único UUID de la ejecución.
@router.get(
    "/runs/{run_id}",
    summary="Detalle de una ejecución",
    responses={
        200: {
            "description": "Detalle de la ejecución encontrada",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "fuente": "ventas",
                        "estado": "COMPLETED",
                        "total_registros": 15,
                        "registros_validos": 10,
                        "registros_error": 5,
                        "duracion_segundos": 1.23,
                        "error_mensaje": None,
                    }
                }
            },
        },
        400: {
            "description": "El run_id proporcionado no es un UUID válido",
            "content": {
                "application/json": {"example": {"detail": "run_id no es un UUID válido"}}
            },
        },
        404: {
            "description": "Ejecución no encontrada",
            "content": {
                "application/json": {"example": {"detail": "Run 550e8400-... no encontrado"}}
            },
        },
    },
)
def get_run(
    # @Parameter (OpenAPI): UUID único que identifica la ejecución del pipeline.
    run_id: str = Path(..., description="Identificador UUID único de la ejecución", example="550e8400-e29b-41d4-a716-446655440000"),
    db: Session = Depends(get_db),
):
    """Obtiene el detalle completo de una ejecución del pipeline por su ID."""
    import uuid as _uuid
    try:
        uid = _uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="run_id no es un UUID válido")

    loader = LoaderStage(db)
    run = loader.get_run(uid)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} no encontrado")

    return {
        "id": str(run.id),
        "fuente": run.fuente,
        "estado": run.estado,
        "fecha_inicio": run.fecha_inicio.isoformat() if run.fecha_inicio else None,
        "fecha_fin": run.fecha_fin.isoformat() if run.fecha_fin else None,
        "total_registros": run.total_registros,
        "registros_validos": run.registros_validos,
        "registros_error": run.registros_error,
        "duracion_segundos": float(run.duracion_segundos) if run.duracion_segundos else None,
        "error_mensaje": run.error_mensaje,
    }


# @Operation (OpenAPI): Retorna el estado consolidado del pipeline por cada fuente de datos.
# @ApiResponses (OpenAPI): Documenta respuesta 200 con el estado actual de cada fuente.
# @Content + @ExampleObject: Ejemplo de la estructura de respuesta por fuente.
@router.get(
    "/status",
    summary="Estado actual del pipeline por fuente",
    responses={
        200: {
            "description": "Estado consolidado por fuente de datos",
            "content": {
                "application/json": {
                    "example": {
                        "ventas": {
                            "fuente": "ventas",
                            "ultimo_estado": "COMPLETED",
                            "ultima_ejecucion": "2026-06-02T12:00:00",
                            "total_runs": 3,
                            "total_registros_procesados": 45,
                            "total_validos": 30,
                            "total_errores": 15,
                        }
                    }
                }
            },
        }
    },
)
def get_pipeline_status(db: Session = Depends(get_db)):
    """Retorna el estado consolidado de cada fuente de datos."""
    from sqlalchemy import func
    from app.models.pipeline_models import PipelineRun

    result = {}
    for source in SOURCES:
        runs = (
            db.query(PipelineRun)
            .filter(PipelineRun.fuente == source)
            .order_by(PipelineRun.fecha_inicio.desc())
            .all()
        )
        last_run = runs[0] if runs else None
        total_registros = sum(r.total_registros or 0 for r in runs)
        total_validos = sum(r.registros_validos or 0 for r in runs)
        total_errores = sum(r.registros_error or 0 for r in runs)

        result[source] = {
            "fuente": source,
            "ultimo_run_id": str(last_run.id) if last_run else None,
            "ultimo_estado": last_run.estado if last_run else "NUNCA_EJECUTADO",
            "ultima_ejecucion": last_run.fecha_inicio.isoformat() if last_run else None,
            "total_runs": len(runs),
            "total_registros_procesados": total_registros,
            "total_validos": total_validos,
            "total_errores": total_errores,
        }
    return result


# @Operation (OpenAPI): Retorna la estructura del grafo del pipeline para visualización frontend.
# @ApiResponses (OpenAPI): Documenta respuestas 200 éxito y 400 fuente inválida.
# @Parameter (OpenAPI): source acepta nombre de fuente o "all" para vista global del pipeline.
# @Content + @ExampleObject: Ejemplo simplificado de nodos y aristas del grafo.
@router.get(
    "/graph/{source}",
    summary="Datos del grafo del pipeline para visualización",
    responses={
        200: {
            "description": "Estructura del grafo con nodos y conexiones del pipeline",
            "content": {
                "application/json": {
                    "example": {
                        "nodes": [{"id": "ingestion", "label": "Ingesta", "tipo": "ingestion", "count": 15}],
                        "edges": [{"source": "ingestion", "target": "validation", "count": 15}],
                        "totales": {"total": 15, "validos": 10, "errores": 5},
                    }
                }
            },
        },
        400: {
            "description": "Fuente no válida",
            "content": {
                "application/json": {"example": {"detail": "Fuente 'xyz' no válida"}}
            },
        },
    },
)
def get_pipeline_graph(
    # @Parameter (OpenAPI): Nombre de la fuente de datos o "all" para ver el pipeline global.
    source: str = Path(..., description="Nombre de la fuente de datos o 'all' para vista global", example="ventas"),
    # @Parameter (OpenAPI): UUID de ejecución específica para filtrar el grafo (opcional).
    run_id: Optional[str] = Query(None, description="UUID de ejecución específica para filtrar el grafo"),
    db: Session = Depends(get_db),
):
    """
    Retorna la estructura del grafo del pipeline para la visualización frontend.
    Incluye nodos, conexiones y contadores por etapa.
    """
    if source not in SOURCES and source != "all":
        raise HTTPException(status_code=400, detail=f"Fuente '{source}' no válida")

    loader = LoaderStage(db)

    if source == "all":
        runs = loader.list_runs(limit=1)
        if not runs:
            total = valid = errors = 0
        else:
            r = runs[0]
            total = r.total_registros or 0
            valid = r.registros_validos or 0
            errors = r.registros_error or 0
    else:
        runs = loader.list_runs(source=source, limit=1)
        if not runs:
            total = valid = errors = 0
        else:
            r = runs[0]
            total = r.total_registros or 0
            valid = r.registros_validos or 0
            errors = r.registros_error or 0

    nodes = [
        {"id": "source",          "label": f"Fuente\n{source.upper()}", "tipo": "source",         "color": "#3B82F6", "count": total},
        {"id": "ingestion",       "label": "Ingesta",                    "tipo": "ingestion",      "color": "#8B5CF6", "count": total},
        {"id": "validation",      "label": "Validación",                 "tipo": "validation",     "color": "#F59E0B", "count": total},
        {"id": "transformation",  "label": "Transformación",             "tipo": "transformation", "color": "#F97316", "count": valid},
        {"id": "classification",  "label": "Clasificación",              "tipo": "classification", "color": "#6366F1", "count": total},
        {"id": "postgresql",      "label": "PostgreSQL",                 "tipo": "database",       "color": "#0EA5E9", "count": total},
        {"id": "clean",           "label": f"Clean\n{valid} registros",  "tipo": "clean",          "color": "#10B981", "count": valid},
        {"id": "error",           "label": f"Error\n{errors} registros", "tipo": "error",          "color": "#EF4444", "count": errors},
    ]

    edges = [
        {"source": "source",         "target": "ingestion",      "label": f"{total}", "count": total},
        {"source": "ingestion",      "target": "validation",     "label": f"{total}", "count": total},
        {"source": "validation",     "target": "transformation", "label": f"{valid} válidos", "count": valid},
        {"source": "validation",     "target": "classification", "label": f"{errors} errores", "count": errors},
        {"source": "transformation", "target": "classification", "label": "",         "count": valid},
        {"source": "classification", "target": "postgresql",     "label": f"{total}", "count": total},
        {"source": "postgresql",     "target": "clean",          "label": f"{valid}", "count": valid},
        {"source": "postgresql",     "target": "error",          "label": f"{errors}", "count": errors},
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "run_id": run_id,
        "fuente": source,
        "totales": {"total": total, "validos": valid, "errores": errors},
    }
