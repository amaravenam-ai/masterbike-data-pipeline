-- ============================================================
-- TABLAS ERROR: Datos rechazados por validación
-- ============================================================

CREATE TABLE IF NOT EXISTS ventas_error (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    fuente VARCHAR(50) DEFAULT 'ventas',
    fecha_ingesta TIMESTAMP DEFAULT NOW(),
    errores_detectados JSONB,
    estado_calidad VARCHAR(50) DEFAULT 'ERROR'
);

CREATE TABLE IF NOT EXISTS usuarios_error (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    fuente VARCHAR(50) DEFAULT 'usuarios',
    fecha_ingesta TIMESTAMP DEFAULT NOW(),
    errores_detectados JSONB,
    estado_calidad VARCHAR(50) DEFAULT 'ERROR'
);

CREATE TABLE IF NOT EXISTS inventario_error (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    fuente VARCHAR(50) DEFAULT 'inventario',
    fecha_ingesta TIMESTAMP DEFAULT NOW(),
    errores_detectados JSONB,
    estado_calidad VARCHAR(50) DEFAULT 'ERROR'
);

CREATE TABLE IF NOT EXISTS arriendos_error (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    fuente VARCHAR(50) DEFAULT 'arriendos',
    fecha_ingesta TIMESTAMP DEFAULT NOW(),
    errores_detectados JSONB,
    estado_calidad VARCHAR(50) DEFAULT 'ERROR'
);

CREATE TABLE IF NOT EXISTS bicicletas_error (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    fuente VARCHAR(50) DEFAULT 'bicicletas',
    fecha_ingesta TIMESTAMP DEFAULT NOW(),
    errores_detectados JSONB,
    estado_calidad VARCHAR(50) DEFAULT 'ERROR'
);

CREATE TABLE IF NOT EXISTS despachos_error (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    fuente VARCHAR(50) DEFAULT 'despachos',
    fecha_ingesta TIMESTAMP DEFAULT NOW(),
    errores_detectados JSONB,
    estado_calidad VARCHAR(50) DEFAULT 'ERROR'
);

CREATE INDEX IF NOT EXISTS idx_ventas_error_run_id ON ventas_error(run_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_error_run_id ON usuarios_error(run_id);
CREATE INDEX IF NOT EXISTS idx_inventario_error_run_id ON inventario_error(run_id);
CREATE INDEX IF NOT EXISTS idx_arriendos_error_run_id ON arriendos_error(run_id);
CREATE INDEX IF NOT EXISTS idx_bicicletas_error_run_id ON bicicletas_error(run_id);
CREATE INDEX IF NOT EXISTS idx_despachos_error_run_id ON despachos_error(run_id);
