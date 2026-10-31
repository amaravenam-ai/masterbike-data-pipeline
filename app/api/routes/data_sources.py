from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.pipeline.loader import LoaderStage
from app.pipeline.ingestion import SOURCES, IngestionStage

router = APIRouter(prefix="/data", tags=["Datos del Pipeline"])

TABLE_TYPES = ["raw", "clean", "error"]


# @Operation (OpenAPI): Lista todas las fuentes de datos disponibles y el estado de sus archivos mock.
# @ApiResponses (OpenAPI): Documenta respuesta 200 con la lista de fuentes y su disponibilidad.
# @Content + @ExampleObject: Ejemplo concreto de la respuesta en Swagger UI.
@router.get(
    "/sources",
    summary="Listar fuentes disponibles",
    responses={
        200: {
            "description": "Lista de fuentes disponibles y estado de archivos mock",
            "content": {
                "application/json": {
                    "example": {
                        "fuentes": ["ventas", "usuarios", "inventario", "arriendos", "bicicletas", "despachos"],
                        "archivos": {
                            "ventas": {"existe": True, "path": "mock_data/ventas.json"},
                            "usuarios": {"existe": True, "path": "mock_data/usuarios.json"},
                        },
                    }
                }
            },
        }
    },
)
def list_sources():
    """Lista todas las fuentes de datos disponibles y el estado de sus archivos mock."""
    ingestion = IngestionStage()
    return {
        "fuentes": SOURCES,
        "archivos": ingestion.list_sources(),
    }


# @Operation (OpenAPI): Consulta los datos almacenados en las tablas raw, clean o error.
# @ApiResponses (OpenAPI): Documenta respuestas posibles:
#   - 200: datos paginados retornados exitosamente.
#   - 400: fuente o tipo de tabla no válido.
# @Parameter (OpenAPI): source y table_type son parámetros de path con valores permitidos documentados.
# @Content + @ExampleObject: Ejemplo de la respuesta paginada con items.
@router.get(
    "/{source}/{table_type}",
    summary="Consultar datos del pipeline",
    responses={
        200: {
            "description": "Datos paginados de la tabla solicitada",
            "content": {
                "application/json": {
                    "example": {
                        "fuente": "ventas",
                        "tipo": "clean",
                        "total": 10,
                        "page": 1,
                        "page_size": 50,
                        "items": [{"registro_id": 1, "data": {"id": 1, "total": 150.00, "estado": "PAGADA"}}],
                    }
                }
            },
        },
        400: {
            "description": "Fuente o tipo de tabla no válido",
            "content": {
                "application/json": {
                    "example": {"detail": "Tipo de tabla 'xyz' no válido. Opciones: ['raw', 'clean', 'error']"}
                }
            },
        },
    },
)
def get_data(
    # @Parameter (OpenAPI): Nombre de la fuente de datos a consultar.
    source: str = Path(..., description="Nombre de la fuente de datos a consultar", example="ventas"),
    # @Parameter (OpenAPI): Tipo de tabla según la etapa del pipeline donde fue almacenado.
    table_type: str = Path(..., description="Tipo de tabla: raw (crudo) | clean (válido transformado) | error (rechazado)", example="clean"),
    # @Parameter (OpenAPI): Número máximo de registros a retornar por página.
    limit: int = Query(50, ge=1, le=500, description="Número máximo de registros a retornar"),
    # @Parameter (OpenAPI): Número de registros a omitir para paginación.
    offset: int = Query(0, ge=0, description="Número de registros a omitir para paginación"),
    db: Session = Depends(get_db),
):
    """
    Consulta los datos almacenados en las tablas del pipeline.

    - **source**: ventas | usuarios | inventario | arriendos | bicicletas | despachos
    - **table_type**: raw | clean | error
    """
    if source not in SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Fuente '{source}' no válida. Disponibles: {SOURCES}",
        )
    if table_type not in TABLE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de tabla '{table_type}' no válido. Opciones: {TABLE_TYPES}",
        )

    loader = LoaderStage(db)
    items = loader.get_data(source, table_type, limit=limit, offset=offset)
    total = loader.count_data(source, table_type)

    return {
        "fuente": source,
        "tipo": table_type,
        "total": total,
        "page": offset // limit + 1,
        "page_size": limit,
        "items": items,
    }


# @Operation (OpenAPI): Retorna el resumen de registros raw, clean y error para una fuente.
# @ApiResponses (OpenAPI): Documenta respuestas:
#   - 200: resumen con conteos y tasa de calidad calculada.
#   - 400: fuente no válida.
# @Parameter (OpenAPI): source es el nombre de la fuente a resumir.
# @Content + @ExampleObject: Ejemplo del JSON de resumen con tasa de calidad.
@router.get(
    "/{source}/summary",
    summary="Resumen de datos por fuente",
    responses={
        200: {
            "description": "Resumen de registros por tipo para la fuente indicada",
            "content": {
                "application/json": {
                    "example": {
                        "fuente": "ventas",
                        "raw": 15,
                        "clean": 10,
                        "error": 5,
                        "tasa_calidad": 66.67,
                    }
                }
            },
        },
        400: {
            "description": "Fuente no válida",
            "content": {
                "application/json": {
                    "example": {"detail": "Fuente 'xyz' no válida. Disponibles: ['ventas', 'usuarios', ...]"}
                }
            },
        },
    },
)
def get_source_summary(
    # @Parameter (OpenAPI): Nombre de la fuente de datos a resumir.
    source: str = Path(..., description="Nombre de la fuente de datos a resumir", example="ventas"),
    db: Session = Depends(get_db),
):
    """Retorna un resumen de registros raw, clean y error para una fuente."""
    if source not in SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Fuente '{source}' no válida. Disponibles: {SOURCES}",
        )

    loader = LoaderStage(db)
    raw_count = loader.count_data(source, "raw")
    clean_count = loader.count_data(source, "clean")
    error_count = loader.count_data(source, "error")

    return {
        "fuente": source,
        "raw": raw_count,
        "clean": clean_count,
        "error": error_count,
        "tasa_calidad": round(clean_count / raw_count * 100, 2) if raw_count > 0 else 0,
    }
