-- ============================================================
-- TABLA: pipeline_runs
-- Registro de cada ejecución del pipeline ETL
-- ============================================================

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fuente VARCHAR(50) NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'RUNNING',
    fecha_inicio TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_fin TIMESTAMP,
    total_registros INTEGER DEFAULT 0,
    registros_validos INTEGER DEFAULT 0,
    registros_error INTEGER DEFAULT 0,
    duracion_segundos NUMERIC(10, 3),
    error_mensaje TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_fuente ON pipeline_runs(fuente);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_estado ON pipeline_runs(estado);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_fecha ON pipeline_runs(fecha_inicio DESC);

COMMENT ON TABLE pipeline_runs IS 'Registro de ejecuciones del pipeline ETL MasterBike';
COMMENT ON COLUMN pipeline_runs.fuente IS 'Módulo origen: ventas, usuarios, inventario, arriendos, bicicletas, despachos';
COMMENT ON COLUMN pipeline_runs.estado IS 'Estado: RUNNING, COMPLETED, FAILED';
