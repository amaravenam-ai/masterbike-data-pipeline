import logging
from datetime import datetime
from typing import Any, Dict, List
from collections import deque

logger = logging.getLogger(__name__)

# Circular buffer para logs en memoria (últimos 500 eventos)
_log_buffer: deque = deque(maxlen=500)

# Métricas en memoria por fuente
_pipeline_metrics: Dict[str, Dict] = {}


class PipelineLogger:
    """Logger estructurado para el pipeline con trazabilidad completa."""

    @staticmethod
    def log_event(
        run_id: str,
        fuente: str,
        stage: str,
        event_type: str,
        message: str,
        data: Dict[str, Any] = None,
        level: str = "INFO",
    ):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": run_id,
            "fuente": fuente,
            "stage": stage,
            "event_type": event_type,
            "message": message,
            "level": level,
            "data": data or {},
        }
        _log_buffer.append(entry)

        log_fn = getattr(logger, level.lower(), logger.info)
        log_fn(f"[{fuente.upper()}][{stage}] {message}", extra={"run_id": run_id})

    @staticmethod
    def log_ingestion_start(run_id: str, fuente: str, source_path: str):
        PipelineLogger.log_event(
            run_id, fuente, "INGESTION", "START",
            f"Iniciando ingesta desde {source_path}",
            {"source_path": source_path},
        )

    @staticmethod
    def log_ingestion_complete(run_id: str, fuente: str, total: int):
        PipelineLogger.log_event(
            run_id, fuente, "INGESTION", "COMPLETE",
            f"Ingesta completada: {total} registros leídos",
            {"total_registros": total},
        )

    @staticmethod
    def log_validation_result(run_id: str, fuente: str, valid: int, errors: int):
        PipelineLogger.log_event(
            run_id, fuente, "VALIDATION", "RESULT",
            f"Validación: {valid} válidos / {errors} con errores",
            {"validos": valid, "errores": errors},
        )

    @staticmethod
    def log_transformation_complete(run_id: str, fuente: str, transformed: int):
        PipelineLogger.log_event(
            run_id, fuente, "TRANSFORMATION", "COMPLETE",
            f"Transformación: {transformed} registros procesados",
            {"transformados": transformed},
        )

    @staticmethod
    def log_load_complete(run_id: str, fuente: str, clean: int, errors: int):
        PipelineLogger.log_event(
            run_id, fuente, "LOAD", "COMPLETE",
            f"Carga en BD: {clean} limpios / {errors} errores guardados",
            {"clean": clean, "errors": errors},
        )

    @staticmethod
    def log_pipeline_error(run_id: str, fuente: str, error: str):
        PipelineLogger.log_event(
            run_id, fuente, "PIPELINE", "ERROR",
            f"Error en pipeline: {error}",
            {"error": error},
            level="ERROR",
        )


def get_recent_logs(limit: int = 100, fuente: str = None) -> List[Dict]:
    logs = list(_log_buffer)
    if fuente:
        logs = [l for l in logs if l.get("fuente") == fuente]
    return list(reversed(logs))[-limit:]


def update_source_metrics(fuente: str, run_data: Dict):
    if fuente not in _pipeline_metrics:
        _pipeline_metrics[fuente] = {
            "total_runs": 0,
            "total_registros": 0,
            "total_validos": 0,
            "total_errores": 0,
            "last_run": None,
        }
    m = _pipeline_metrics[fuente]
    m["total_runs"] += 1
    m["total_registros"] += run_data.get("total_registros", 0)
    m["total_validos"] += run_data.get("registros_validos", 0)
    m["total_errores"] += run_data.get("registros_error", 0)
    m["last_run"] = datetime.utcnow().isoformat()


def get_all_metrics() -> Dict:
    return {
        "fuentes": _pipeline_metrics,
        "total_logs_en_buffer": len(_log_buffer),
        "timestamp": datetime.utcnow().isoformat(),
    }
