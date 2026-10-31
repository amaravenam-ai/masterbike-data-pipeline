import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database.connection import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fuente = Column(String(50), nullable=False)
    estado = Column(String(50), nullable=False, default="RUNNING")
    fecha_inicio = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_fin = Column(DateTime, nullable=True)
    total_registros = Column(Integer, default=0)
    registros_validos = Column(Integer, default=0)
    registros_error = Column(Integer, default=0)
    duracion_segundos = Column(Numeric(10, 3), nullable=True)
    error_mensaje = Column(Text, nullable=True)
    metadata_ = Column("pipeline_metadata", JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Tablas RAW ───────────────────────────────────────────────────────────────

class VentasRaw(Base):
    __tablename__ = "ventas_raw"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    fuente = Column(String(50), default="ventas")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)


class UsuariosRaw(Base):
    __tablename__ = "usuarios_raw"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    fuente = Column(String(50), default="usuarios")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)


class InventarioRaw(Base):
    __tablename__ = "inventario_raw"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    fuente = Column(String(50), default="inventario")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)


class ArriendosRaw(Base):
    __tablename__ = "arriendos_raw"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    fuente = Column(String(50), default="arriendos")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)


class BicicletasRaw(Base):
    __tablename__ = "bicicletas_raw"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    fuente = Column(String(50), default="bicicletas")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)


class DespachosRaw(Base):
    __tablename__ = "despachos_raw"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    fuente = Column(String(50), default="despachos")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)


# ── Tablas CLEAN ─────────────────────────────────────────────────────────────

class VentasClean(Base):
    __tablename__ = "ventas_clean"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    data_original = Column(JSONB)
    fuente = Column(String(50), default="ventas")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)
    transformaciones_aplicadas = Column(JSONB)
    estado_calidad = Column(String(50), default="VALID")


class UsuariosClean(Base):
    __tablename__ = "usuarios_clean"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    data_original = Column(JSONB)
    fuente = Column(String(50), default="usuarios")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)
    transformaciones_aplicadas = Column(JSONB)
    estado_calidad = Column(String(50), default="VALID")


class InventarioClean(Base):
    __tablename__ = "inventario_clean"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    data_original = Column(JSONB)
    fuente = Column(String(50), default="inventario")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)
    transformaciones_aplicadas = Column(JSONB)
    estado_calidad = Column(String(50), default="VALID")


class ArriendosClean(Base):
    __tablename__ = "arriendos_clean"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    data_original = Column(JSONB)
    fuente = Column(String(50), default="arriendos")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)
    transformaciones_aplicadas = Column(JSONB)
    estado_calidad = Column(String(50), default="VALID")


class BicicletasClean(Base):
    __tablename__ = "bicicletas_clean"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    data_original = Column(JSONB)
    fuente = Column(String(50), default="bicicletas")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)
    transformaciones_aplicadas = Column(JSONB)
    estado_calidad = Column(String(50), default="VALID")


class DespachosClean(Base):
    __tablename__ = "despachos_clean"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    data_original = Column(JSONB)
    fuente = Column(String(50), default="despachos")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)
    transformaciones_aplicadas = Column(JSONB)
    estado_calidad = Column(String(50), default="VALID")


# ── Tablas ERROR ─────────────────────────────────────────────────────────────

class VentasError(Base):
    __tablename__ = "ventas_error"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    fuente = Column(String(50), default="ventas")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)
    errores_detectados = Column(JSONB)
    estado_calidad = Column(String(50), default="ERROR")


class UsuariosError(Base):
    __tablename__ = "usuarios_error"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    fuente = Column(String(50), default="usuarios")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)
    errores_detectados = Column(JSONB)
    estado_calidad = Column(String(50), default="ERROR")


class InventarioError(Base):
    __tablename__ = "inventario_error"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    fuente = Column(String(50), default="inventario")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)
    errores_detectados = Column(JSONB)
    estado_calidad = Column(String(50), default="ERROR")


class ArriendosError(Base):
    __tablename__ = "arriendos_error"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    fuente = Column(String(50), default="arriendos")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)
    errores_detectados = Column(JSONB)
    estado_calidad = Column(String(50), default="ERROR")


class BicicletasError(Base):
    __tablename__ = "bicicletas_error"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    fuente = Column(String(50), default="bicicletas")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)
    errores_detectados = Column(JSONB)
    estado_calidad = Column(String(50), default="ERROR")


class DespachosError(Base):
    __tablename__ = "despachos_error"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    registro_id = Column(String(100))
    data = Column(JSONB, nullable=False)
    fuente = Column(String(50), default="despachos")
    fecha_ingesta = Column(DateTime, default=datetime.utcnow)
    errores_detectados = Column(JSONB)
    estado_calidad = Column(String(50), default="ERROR")
