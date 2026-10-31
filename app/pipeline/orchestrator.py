import uuid
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.pipeline.ingestion import IngestionStage
from app.pipeline.validation_stage import ValidationStage
from app.pipeline.transformation_stage import TransformationStage
from app.pipeline.loader import LoaderStage
from app.monitoring.metrics import PipelineLogger, update_source_metrics

logger = logging.getLogger(__name__)


class PipelineResult:
    """Resultado completo de una ejecución del pipeline."""

    def __init__(
        self,
        run_id: uuid.UUID,
        fuente: str,
        estado: str,
        total_registros: int,
        registros_validos: int,
        registros_error: int,
        duracion_segundos: float,
        stages: List[Dict],
        error_mensaje: Optional[str] = None,
    ):
        self.run_id = run_id
        self.fuente = fuente
        self.estado = estado
        self.total_registros = total_registros
        self.registros_validos = registros_validos
        self.registros_error = registros_error
        self.duracion_segundos = duracion_segundos
        self.stages = stages
        self.error_mensaje = error_mensaje

    def to_dict(self) -> Dict:
        return {
            "run_id": str(self.run_id),
            "fuente": self.fuente,
            "estado": self.estado,
            "total_registros": self.total_registros,
            "registros_validos": self.registros_validos,
            "registros_error": self.registros_error,
            "duracion_segundos": self.duracion_segundos,
            "tasa_exito": (
                round(self.registros_validos / self.total_registros * 100, 2)
                if self.total_registros > 0
                else 0
            ),
            "stages": self.stages,
            "error_mensaje": self.error_mensaje,
        }


class PipelineOrchestrator:
    """
    Orquestador del pipeline ETL MasterBike.

    Coordina las etapas:
    INGESTION → VALIDATION → TRANSFORMATION → LOAD (clean + error)
    """

    def __init__(self, db: Session):
        self.db = db
        self.ingestion = IngestionStage()
        self.validator = ValidationStage()
        self.transformer = TransformationStage()
        self.loader = LoaderStage(db)

    def run(self, source: str) -> PipelineResult:
        run_id = uuid.uuid4()
        start_time = datetime.utcnow()
        stages = []

        PipelineLogger.log_event(
            str(run_id), source, "PIPELINE", "START",
            f"=== Iniciando pipeline para fuente: {source.upper()} ===",
        )

        pipeline_run = self.loader.create_run(run_id, source, start_time)

        try:
            # ── Etapa 1: INGESTION ───────────────────────────────────────────
            t0 = time.time()
            PipelineLogger.log_ingestion_start(str(run_id), source, f"mock_data/{source}.json")
            raw_records = self.ingestion.ingest(source)
            ingestion_ms = round((time.time() - t0) * 1000, 2)

            PipelineLogger.log_ingestion_complete(str(run_id), source, len(raw_records))
            stages.append({
                "stage": "INGESTION",
                "registros_entrada": 0,
                "registros_salida": len(raw_records),
                "registros_descartados": 0,
                "duracion_ms": ingestion_ms,
            })

            # Guardar datos crudos en PostgreSQL
            self.loader.save_raw(raw_records, run_id, source)

            # ── Etapa 2: VALIDATION ──────────────────────────────────────────
            t0 = time.time()
            valid_records, error_records = self.validator.validate(raw_records, source)
            validation_ms = round((time.time() - t0) * 1000, 2)

            PipelineLogger.log_validation_result(
                str(run_id), source, len(valid_records), len(error_records)
            )
            stages.append({
                "stage": "VALIDATION",
                "registros_entrada": len(raw_records),
                "registros_salida": len(valid_records),
                "registros_descartados": len(error_records),
                "duracion_ms": validation_ms,
            })

            # ── Etapa 3: TRANSFORMATION ──────────────────────────────────────
            t0 = time.time()
            transformed_records = self.transformer.transform(valid_records, source)
            transformation_ms = round((time.time() - t0) * 1000, 2)

            PipelineLogger.log_transformation_complete(
                str(run_id), source, len(transformed_records)
            )
            stages.append({
                "stage": "TRANSFORMATION",
                "registros_entrada": len(valid_records),
                "registros_salida": len(transformed_records),
                "registros_descartados": 0,
                "duracion_ms": transformation_ms,
            })

            # ── Etapa 4: LOAD ────────────────────────────────────────────────
            t0 = time.time()
            self.loader.save_clean(transformed_records, run_id, source)
            self.loader.save_errors(error_records, run_id, source)
            load_ms = round((time.time() - t0) * 1000, 2)

            PipelineLogger.log_load_complete(
                str(run_id), source, len(transformed_records), len(error_records)
            )
            stages.append({
                "stage": "LOAD",
                "registros_entrada": len(transformed_records) + len(error_records),
                "registros_salida": len(transformed_records) + len(error_records),
                "registros_descartados": 0,
                "duracion_ms": load_ms,
            })

            # ── Finalizar run ────────────────────────────────────────────────
            end_time = datetime.utcnow()
            self.loader.complete_run(
                pipeline_run,
                len(raw_records),
                len(transformed_records),
                len(error_records),
                end_time,
            )

            duracion = (end_time - start_time).total_seconds()
            update_source_metrics(source, {
                "total_registros": len(raw_records),
                "registros_validos": len(transformed_records),
                "registros_error": len(error_records),
            })

            PipelineLogger.log_event(
                str(run_id), source, "PIPELINE", "COMPLETE",
                f"Pipeline completado en {duracion:.3f}s | "
                f"{len(raw_records)} total | {len(transformed_records)} válidos | "
                f"{len(error_records)} errores",
            )

            return PipelineResult(
                run_id=run_id,
                fuente=source,
                estado="COMPLETED",
                total_registros=len(raw_records),
                registros_validos=len(transformed_records),
                registros_error=len(error_records),
                duracion_segundos=round(duracion, 3),
                stages=stages,
            )

        except Exception as exc:
            self.loader.fail_run(pipeline_run, str(exc))
            PipelineLogger.log_pipeline_error(str(run_id), source, str(exc))
            logger.exception(f"Pipeline fallido para fuente '{source}': {exc}")

            return PipelineResult(
                run_id=run_id,
                fuente=source,
                estado="FAILED",
                total_registros=0,
                registros_validos=0,
                registros_error=0,
                duracion_segundos=round((datetime.utcnow() - start_time).total_seconds(), 3),
                stages=stages,
                error_mensaje=str(exc),
            )
