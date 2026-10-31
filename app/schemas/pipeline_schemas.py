from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID


# @Schema (OpenAPI): Documenta el modelo de respuesta de una ejecución del pipeline.
# Equivale a @Schema(description="...") aplicado a la clase en Springdoc.
# Cada campo usa Field(description=..., example=...) para documentar propiedades individuales,
# lo que equivale a @Schema(description="...", example="...") por campo en Java.
class PipelineRunResponse(BaseModel):
    id: UUID = Field(..., description="Identificador único UUID de la ejecución", example="12345")
    fuente: str = Field(..., description="Fuente de datos procesada", example="ventas")
    estado: str = Field(..., description="Estado de la ejecución: COMPLETED, FAILED, RUNNING", example="COMPLETED")
    fecha_inicio: datetime = Field(..., description="Fecha y hora de inicio de la ejecución")
    fecha_fin: Optional[datetime] = Field(None, description="Fecha y hora de fin; null si aún está en ejecución")
    total_registros: int = Field(0, description="Total de registros ingresados al pipeline", example=15)
    registros_validos: int = Field(0, description="Registros que pasaron la validación correctamente", example=10)
    registros_error: int = Field(0, description="Registros rechazados por errores de validación", example=5)
    duracion_segundos: Optional[float] = Field(None, description="Duración total de la ejecución en segundos", example=1.23)
    error_mensaje: Optional[str] = Field(None, description="Mensaje de error si el pipeline falló; null si fue exitoso")

    model_config = {"from_attributes": True}


# @Schema (OpenAPI): Documenta las métricas de una etapa individual del pipeline.
class PipelineStageMetrics(BaseModel):
    stage: str = Field(..., description="Nombre de la etapa: ingestion, validation, transformation, load", example="validation")
    registros_entrada: int = Field(..., description="Registros que entraron a esta etapa", example=15)
    registros_salida: int = Field(..., description="Registros que salieron exitosamente de esta etapa", example=10)
    registros_descartados: int = Field(..., description="Registros descartados en esta etapa", example=5)
    duracion_ms: float = Field(..., description="Duración de la etapa en milisegundos", example=42.5)


# @Schema (OpenAPI): Detalle completo de una ejecución incluyendo métricas por etapa.
class PipelineRunDetail(BaseModel):
    run: PipelineRunResponse = Field(..., description="Datos generales de la ejecución")
    stages: List[PipelineStageMetrics] = Field(..., description="Métricas desglosadas por cada etapa del pipeline")
    tasa_exito: float = Field(..., description="Porcentaje de registros válidos sobre el total", example=66.67)
    tasa_error: float = Field(..., description="Porcentaje de registros con error sobre el total", example=33.33)


# @Schema (OpenAPI): Estado consolidado de una fuente de datos.
class PipelineStatusResponse(BaseModel):
    fuente: str = Field(..., description="Nombre de la fuente de datos", example="ventas")
    ultimo_run_id: Optional[UUID] = Field(None, description="UUID de la última ejecución registrada")
    ultimo_estado: Optional[str] = Field(None, description="Estado de la última ejecución", example="COMPLETED")
    ultima_ejecucion: Optional[datetime] = Field(None, description="Timestamp de la última ejecución")
    total_runs: int = Field(..., description="Número total de ejecuciones realizadas para esta fuente", example=3)
    total_registros_procesados: int = Field(..., description="Total acumulado de registros procesados", example=45)
    total_validos: int = Field(..., description="Total acumulado de registros válidos", example=30)
    total_errores: int = Field(..., description="Total acumulado de registros con error", example=15)


# @Schema (OpenAPI): Nodo del grafo de visualización del pipeline.
class PipelineGraphNode(BaseModel):
    id: str = Field(..., description="Identificador único del nodo", example="validation")
    label: str = Field(..., description="Etiqueta visible en el grafo", example="Validación")
    tipo: str = Field(..., description="Tipo del nodo: source, ingestion, validation, transformation, database, clean, error", example="validation")
    color: str = Field(..., description="Color hexadecimal del nodo en la visualización", example="#F59E0B")
    count: int = Field(0, description="Cantidad de registros en este nodo", example=15)


# @Schema (OpenAPI): Arista (conexión) del grafo de visualización del pipeline.
class PipelineGraphEdge(BaseModel):
    source: str = Field(..., description="ID del nodo de origen", example="ingestion")
    target: str = Field(..., description="ID del nodo de destino", example="validation")
    label: str = Field("", description="Etiqueta de la conexión, generalmente el conteo de registros", example="15")
    count: int = Field(0, description="Cantidad de registros que fluyen por esta conexión", example=15)


# @Schema (OpenAPI): Estructura completa del grafo del pipeline para visualización frontend.
# @ArraySchema equivalente: nodes y edges son listas de objetos tipados (List[PipelineGraphNode]).
class PipelineGraphResponse(BaseModel):
    nodes: List[PipelineGraphNode] = Field(..., description="Lista de nodos del grafo")
    edges: List[PipelineGraphEdge] = Field(..., description="Lista de conexiones entre nodos")
    run_id: Optional[str] = Field(None, description="UUID de la ejecución asociada")
    fuente: Optional[str] = Field(None, description="Fuente de datos representada en el grafo", example="ventas")


# @Schema (OpenAPI): Respuesta paginada de datos del pipeline (raw, clean o error).
class DataPageResponse(BaseModel):
    fuente: str = Field(..., description="Fuente de datos consultada", example="ventas")
    tipo: str = Field(..., description="Tipo de tabla consultada: raw | clean | error", example="clean")
    total: int = Field(..., description="Total de registros disponibles en la tabla", example=10)
    page: int = Field(..., description="Número de página actual (basado en offset/limit)", example=1)
    page_size: int = Field(..., description="Tamaño de página solicitado", example=50)
    items: List[Dict[str, Any]] = Field(..., description="Registros de la página actual")


# @Schema (OpenAPI): Respuesta de la ejecución de todos los pipelines en lote.
# @ArraySchema equivalente: resultados es una lista de PipelineRunResponse tipados.
class RunAllResponse(BaseModel):
    total_fuentes: int = Field(..., description="Número de fuentes procesadas", example=6)
    resultados: List[PipelineRunResponse] = Field(..., description="Resultado individual de cada fuente procesada")
    total_registros: int = Field(..., description="Total acumulado de registros procesados en todas las fuentes", example=75)
    total_validos: int = Field(..., description="Total acumulado de registros válidos en todas las fuentes", example=57)
    total_errores: int = Field(..., description="Total acumulado de registros con error en todas las fuentes", example=18)
    duracion_total_segundos: float = Field(..., description="Tiempo total de procesamiento en segundos", example=4.56)


# @Schema (OpenAPI): Respuesta del health check del sistema.
class HealthResponse(BaseModel):
    status: str = Field(..., description="Estado general del sistema: healthy | degraded", example="healthy")
    database: str = Field(..., description="Estado de la conexión a PostgreSQL: connected | disconnected", example="connected")
    timestamp: datetime = Field(..., description="Timestamp del momento en que se realizó el health check")
    version: str = Field("1.0.0", description="Versión de la aplicación", example="1.0.0")
