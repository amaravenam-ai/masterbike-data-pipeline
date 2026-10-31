import logging
import os
import time as _time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.openapi.docs import get_swagger_ui_html
from sqlalchemy.orm import Session

from app.database.connection import init_db, get_db
from app.api.routes.pipeline import router as pipeline_router
from app.api.routes.monitoring import router as monitoring_router
from app.api.routes.data_sources import router as data_router
from app.api.routes.performance import router as performance_router
from app.api.routes.security import router as security_router

# Configurar logging estructurado
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("  MasterBike Data Pipeline Platform v1.0.0")
    logger.info("=" * 60)
    logger.info("Inicializando base de datos...")
    init_db()
    logger.info("Sistema listo. Todos los módulos inicializados.")
    yield
    logger.info("Cerrando MasterBike Data Pipeline Platform...")


app = FastAPI(
    title="MasterBike Data Pipeline Platform",
    description="""
## Plataforma ETL de Ingeniería de Datos - MasterBike

Sistema de pipeline de datos para ingesta, validación, transformación y carga
de datos de todos los módulos del ecosistema MasterBike.

### Módulos soportados
- **Ventas**: Transacciones de venta a clientes
- **Usuarios**: Usuarios del sistema (administradores, técnicos, vendedores)
- **Inventario**: Stock de productos y repuestos
- **Arriendos**: Arriendos de bicicletas
- **Bicicletas**: Catálogo de bicicletas
- **Despachos**: Seguimiento de entregas

### Pipeline ETL
```
[Fuente] → [Ingesta] → [Validación] → [Transformación] → [PostgreSQL]
                                                            ↙         ↘
                                                        [Clean]     [Error]
```
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Registrar rutas de la API
app.include_router(pipeline_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")
app.include_router(data_router, prefix="/api/v1")
app.include_router(performance_router)
app.include_router(security_router)

# Servir frontend estático
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "static")), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse(os.path.join(frontend_path, "index.html"))


    @app.get("/dashboard", include_in_schema=False)
    def serve_dashboard():
        return FileResponse(os.path.join(frontend_path, "index.html"))


@app.get("/docs", include_in_schema=False)
def swagger_docs_alias():
    return get_swagger_ui_html(openapi_url=app.openapi_url, title=f"{app.title} - Swagger UI")


@app.get("/api/pipeline/status", tags=["Pipeline Status"], summary="Estado detallado del último pipeline ejecutado")
def get_pipeline_status_detail(
    source: str = Query("ventas", description="Fuente de datos: ventas, usuarios, inventario, arriendos, bicicletas, despachos"),
    db: Session = Depends(get_db),
):
    """
    Retorna las métricas REALES del último pipeline ejecutado para la fuente indicada.

    Incluye estado, contadores reales por etapa y tiempo de ejecución.

    Etapas devueltas: **Fuente → Ingesta → Validación → Transformación → PostgreSQL → Clean / Error**
    """
    from app.models.pipeline_models import PipelineRun
    from app.pipeline.loader import MODEL_MAP
    from app.pipeline.ingestion import SOURCES

    FUENTES_VALIDAS = list(SOURCES)
    if source not in FUENTES_VALIDAS:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Fuente '{source}' no válida. Opciones: {FUENTES_VALIDAS}",
        )

    t_inicio = _time.time()

    # Último run para la fuente solicitada
    last_run = (
        db.query(PipelineRun)
        .filter(PipelineRun.fuente == source)
        .order_by(PipelineRun.fecha_inicio.desc())
        .first()
    )

    # Sin datos aún
    if not last_run:
        return {
            "estado": "SIN_DATOS",
            "fuente": source,
            "run_id": None,
            "registros_procesados": 0,
            "registros_validos": 0,
            "registros_error": 0,
            "tiempo_ejecucion": 0.0,
            "ultima_ejecucion": None,
            "tasa_calidad": 0.0,
            "etapas": {
                "fuente":        {"nombre": "Fuente",         "registros": 0,  "descripcion": f"{source}.json",        "estado": "sin_datos"},
                "ingesta":       {"nombre": "Ingesta",        "registros": 0,  "descripcion": "Sin registros leídos",  "estado": "sin_datos"},
                "validacion":    {"nombre": "Validación",     "validos": 0,    "errores": 0,  "tasa_calidad": 0.0,    "estado": "sin_datos"},
                "transformacion":{"nombre": "Transformación", "registros": 0,  "descripcion": "Sin transformaciones",  "estado": "sin_datos"},
                "postgresql":    {"nombre": "PostgreSQL",     "registros": 0,  "descripcion": "Sin datos guardados",   "estado": "sin_datos"},
                "clean":         {"nombre": "Clean",          "registros": 0,  "descripcion": "0 registros válidos",   "estado": "sin_datos"},
                "error":         {"nombre": "Error",          "registros": 0,  "descripcion": "0 registros con error", "estado": "sin_datos"},
            },
        }

    duracion = float(last_run.duracion_segundos) if last_run.duracion_segundos else 0.0

    # Conteo REAL desde tablas clean y error para este run_id
    _, CleanModel, ErrorModel = MODEL_MAP[source]
    clean_count = db.query(CleanModel).filter(CleanModel.run_id == last_run.id).count()
    error_count = db.query(ErrorModel).filter(ErrorModel.run_id == last_run.id).count()

    # Conteo real raw (tabla de ingesta)
    RawModel, _, _ = MODEL_MAP[source]
    raw_count = db.query(RawModel).filter(RawModel.run_id == last_run.id).count()

    # Cero también es un conteo real: no sustituirlo por métricas históricas.
    total_real = raw_count
    validos_real = clean_count
    error_real = error_count

    tasa_real = round(validos_real / total_real * 100, 2) if total_real > 0 else 0.0

    estado_pg = "guardado" if last_run.estado == "COMPLETED" else ("fallido" if last_run.estado == "FAILED" else "en_proceso")

    return {
        "estado": last_run.estado,
        "fuente": source,
        "run_id": str(last_run.id),
        "registros_procesados": total_real,
        "registros_validos":    validos_real,
        "registros_error":      error_real,
        "tiempo_ejecucion":     duracion,
        "ultima_ejecucion":     last_run.fecha_inicio.isoformat() if last_run.fecha_inicio else None,
        "tasa_calidad":         tasa_real,
        "consulta_ms":          round((_time.time() - t_inicio) * 1000, 2),
        "etapas": {
            "fuente": {
                "nombre":      "Fuente",
                "registros":   total_real,
                "descripcion": f"mock_data/{source}.json",
                "estado":      "ok",
            },
            "ingesta": {
                "nombre":      "Ingesta",
                "registros":   total_real,
                "descripcion": f"{total_real} registros leídos",
                "estado":      "ok" if total_real > 0 else "sin_datos",
            },
            "validacion": {
                "nombre":       "Validación",
                "validos":      validos_real,
                "errores":      error_real,
                "tasa_calidad": tasa_real,
                "estado":       "ok" if total_real > 0 else "sin_datos",
            },
            "transformacion": {
                "nombre":      "Transformación",
                "registros":   validos_real,
                "descripcion": f"{validos_real} registros transformados",
                "estado":      "ok" if validos_real > 0 else "sin_datos",
            },
            "postgresql": {
                "nombre":      "PostgreSQL",
                "registros":   total_real,
                "descripcion": "Guardado correcto" if estado_pg == "guardado" else "Error al guardar",
                "estado":      estado_pg,
            },
            "clean": {
                "nombre":      "Clean",
                "registros":   validos_real,
                "descripcion": f"{validos_real} registros válidos",
                "estado":      "ok" if validos_real > 0 else "sin_datos",
            },
            "error": {
                "nombre":      "Error",
                "registros":   error_real,
                "descripcion": f"{error_real} registros con errores",
                "estado":      "ok" if error_real >= 0 else "sin_datos",
            },
        },
    }


@app.get("/api", tags=["Root"])
def api_info():
    """Información general de la API del pipeline."""
    return {
        "name": "MasterBike Data Pipeline Platform",
        "version": "1.0.0",
        "description": "Plataforma ETL de ingeniería de datos para el ecosistema MasterBike",
        "docs": "/api/docs",
        "dashboard": "/",
        "fuentes": ["ventas", "usuarios", "inventario", "arriendos", "bicicletas", "despachos"],
        "endpoints": {
            "pipeline": "/api/v1/pipeline",
            "monitoring": "/api/v1/monitoring",
            "data": "/api/v1/data",
            "performance": "/api/performance",
            "security": "/api/security",
        },
    }
