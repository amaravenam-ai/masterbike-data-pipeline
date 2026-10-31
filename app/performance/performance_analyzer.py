import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import psutil
from sqlalchemy.orm import Session

from app.performance.report_writer import write_performance_report
from app.pipeline.ingestion import SOURCES
from app.pipeline.orchestrator import PipelineOrchestrator, PipelineResult


class PerformanceAnalyzer:
    """Runs the existing ETL and captures simple runtime metrics."""

    def __init__(self, db: Session):
        self.db = db
        self.process = psutil.Process()

    def run(self, source: str = "all") -> Dict[str, Any]:
        sources = self._resolve_sources(source)
        orchestrator = PipelineOrchestrator(self.db)

        self.process.cpu_percent(interval=None)
        start = time.time()
        results: List[PipelineResult] = []

        for item in sources:
            results.append(orchestrator.run(item))

        execution_time = round(time.time() - start, 3)
        cpu_percent = round(self.process.cpu_percent(interval=0.1), 2)
        memory_mb = round(self.process.memory_info().rss / (1024 * 1024), 2)

        total_records = sum(r.total_registros for r in results)
        valid_records = sum(r.registros_validos for r in results)
        error_records = sum(r.registros_error for r in results)
        status = "COMPLETED" if all(r.estado == "COMPLETED" for r in results) else "FAILED"
        slowest_stage = self._find_slowest_stage(results)

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "source": source,
            "execution_time_seconds": execution_time,
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
            "total_records": total_records,
            "valid_records": valid_records,
            "error_records": error_records,
            "status": status,
            "slowest_stage": slowest_stage,
            "recommendation": self._build_recommendation(
                status=status,
                error_records=error_records,
                slowest_stage=slowest_stage,
            ),
            "runs": [self._result_to_dict(r) for r in results],
        }
        report["report_files"] = write_performance_report(report)
        return report

    def _resolve_sources(self, source: str) -> List[str]:
        if source == "all":
            return list(SOURCES)
        if source not in SOURCES:
            raise ValueError(f"Fuente invalida: {source}. Opciones: all, {', '.join(SOURCES)}")
        return [source]

    def _find_slowest_stage(self, results: List[PipelineResult]) -> Dict[str, Any]:
        slowest: Optional[Dict[str, Any]] = None

        for result in results:
            for stage in result.stages:
                candidate = {
                    "source": result.fuente,
                    "stage": stage.get("stage"),
                    "duration_ms": stage.get("duracion_ms", 0),
                }
                if slowest is None or candidate["duration_ms"] > slowest["duration_ms"]:
                    slowest = candidate

        return slowest or {"source": None, "stage": None, "duration_ms": 0}

    def _build_recommendation(
        self,
        status: str,
        error_records: int,
        slowest_stage: Dict[str, Any],
    ) -> str:
        if status != "COMPLETED":
            return "Revisar logs del pipeline antes de optimizar rendimiento."

        stage = slowest_stage.get("stage")
        if stage == "LOAD":
            return "La carga fue la etapa mas lenta; revisar indices, commits por lote y conexion a PostgreSQL."
        if stage == "VALIDATION":
            return "La validacion fue la etapa mas lenta; revisar reglas repetidas y validar por lotes si aumenta el volumen."
        if stage == "TRANSFORMATION":
            return "La transformacion fue la etapa mas lenta; revisar calculos derivados y normalizaciones repetidas."
        if error_records > 0:
            return "Hay registros rechazados; revisar la calidad de datos de origen para reducir reprocesos."
        return "Rendimiento estable para el volumen actual; seguir midiendo al aumentar datos."

    def _result_to_dict(self, result: PipelineResult) -> Dict[str, Any]:
        data = result.to_dict()
        data["stages"] = result.stages
        return data
