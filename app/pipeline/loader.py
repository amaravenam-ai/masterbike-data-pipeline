import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.pipeline_models import (
    PipelineRun,
    VentasRaw, VentasClean, VentasError,
    UsuariosRaw, UsuariosClean, UsuariosError,
    InventarioRaw, InventarioClean, InventarioError,
    ArriendosRaw, ArriendosClean, ArriendosError,
    BicicletasRaw, BicicletasClean, BicicletasError,
    DespachosRaw, DespachosClean, DespachosError,
)

logger = logging.getLogger(__name__)

# Mapeo de fuente -> clases de modelo (raw, clean, error)
MODEL_MAP = {
    "ventas":     (VentasRaw,     VentasClean,     VentasError),
    "usuarios":   (UsuariosRaw,   UsuariosClean,   UsuariosError),
    "inventario": (InventarioRaw, InventarioClean, InventarioError),
    "arriendos":  (ArriendosRaw,  ArriendosClean,  ArriendosError),
    "bicicletas": (BicicletasRaw, BicicletasClean, BicicletasError),
    "despachos":  (DespachosRaw,  DespachosClean,  DespachosError),
}


class LoaderStage:
    """Etapa de carga: persiste datos en PostgreSQL."""

    def __init__(self, db: Session):
        self.db = db

    def create_run(self, run_id: uuid.UUID, source: str, start_time: datetime) -> PipelineRun:
        run = PipelineRun(
            id=run_id,
            fuente=source,
            estado="RUNNING",
            fecha_inicio=start_time,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def save_raw(self, records: List[Dict], run_id: uuid.UUID, source: str):
        RawModel, _, _ = MODEL_MAP[source]
        for record in records:
            row = RawModel(
                run_id=run_id,
                registro_id=str(record.get("id", "")),
                data=record,
                fuente=source,
                fecha_ingesta=datetime.utcnow(),
            )
            self.db.add(row)
        self.db.commit()
        logger.info(f"[LOAD][RAW][{source.upper()}] {len(records)} registros guardados")

    def save_clean(self, transformed_records: List[Dict], run_id: uuid.UUID, source: str):
        _, CleanModel, _ = MODEL_MAP[source]
        for item in transformed_records:
            row = CleanModel(
                run_id=run_id,
                registro_id=str(item["data"].get("id", "")),
                data=item["data"],
                data_original=item["data_original"],
                fuente=source,
                fecha_ingesta=datetime.utcnow(),
                transformaciones_aplicadas=item["transformaciones_aplicadas"],
                estado_calidad="VALID",
            )
            self.db.add(row)
        self.db.commit()
        logger.info(f"[LOAD][CLEAN][{source.upper()}] {len(transformed_records)} registros guardados")

    def save_errors(self, error_records: List[Dict], run_id: uuid.UUID, source: str):
        _, _, ErrorModel = MODEL_MAP[source]
        for record in error_records:
            record = dict(record)
            errores = record.pop("_errores_detectados", [])
            row = ErrorModel(
                run_id=run_id,
                registro_id=str(record.get("id", "")),
                data=record,
                fuente=source,
                fecha_ingesta=datetime.utcnow(),
                errores_detectados=errores,
                estado_calidad="ERROR",
            )
            self.db.add(row)
        self.db.commit()
        logger.info(f"[LOAD][ERROR][{source.upper()}] {len(error_records)} registros guardados")

    def complete_run(
        self,
        run: PipelineRun,
        total: int,
        validos: int,
        errores: int,
        end_time: datetime,
    ):
        duracion = (end_time - run.fecha_inicio).total_seconds()
        run.estado = "COMPLETED"
        run.fecha_fin = end_time
        run.total_registros = total
        run.registros_validos = validos
        run.registros_error = errores
        run.duracion_segundos = round(duracion, 3)
        self.db.commit()
        self.db.refresh(run)

    def fail_run(self, run: PipelineRun, error_msg: str):
        self.db.rollback()
        run.estado = "FAILED"
        run.fecha_fin = datetime.utcnow()
        run.error_mensaje = error_msg
        self.db.commit()

    def get_run(self, run_id: uuid.UUID) -> Optional[PipelineRun]:
        return self.db.query(PipelineRun).filter(PipelineRun.id == run_id).first()

    def list_runs(
        self, source: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> List[PipelineRun]:
        q = self.db.query(PipelineRun)
        if source:
            q = q.filter(PipelineRun.fuente == source)
        return q.order_by(PipelineRun.fecha_inicio.desc()).offset(offset).limit(limit).all()

    def get_data(
        self, source: str, table_type: str, limit: int = 100, offset: int = 0
    ) -> List[Dict]:
        if table_type == "raw":
            Model, _, _ = MODEL_MAP[source]
        elif table_type == "clean":
            _, Model, _ = MODEL_MAP[source]
        elif table_type == "error":
            _, _, Model = MODEL_MAP[source]
        else:
            raise ValueError(f"Tipo de tabla inválido: {table_type}")

        rows = (
            self.db.query(Model)
            .order_by(Model.fecha_ingesta.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "run_id": str(r.run_id),
                "registro_id": r.registro_id,
                "data": r.data,
                "fuente": r.fuente,
                "fecha_ingesta": r.fecha_ingesta.isoformat() if r.fecha_ingesta else None,
                **({"transformaciones_aplicadas": r.transformaciones_aplicadas, "estado_calidad": r.estado_calidad} if table_type == "clean" else {}),
                **({"errores_detectados": r.errores_detectados, "estado_calidad": r.estado_calidad} if table_type == "error" else {}),
            }
            for r in rows
        ]

    def count_data(self, source: str, table_type: str) -> int:
        if table_type == "raw":
            Model, _, _ = MODEL_MAP[source]
        elif table_type == "clean":
            _, Model, _ = MODEL_MAP[source]
        elif table_type == "error":
            _, _, Model = MODEL_MAP[source]
        else:
            return 0
        return self.db.query(Model).count()
