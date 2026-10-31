-- ============================================================
-- TABLAS RAW: Datos sin procesar ingresados al pipeline
-- Una tabla por módulo MasterBike
-- ============================================================

CREATE TABLE IF NOT EXISTS ventas_raw (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    fuente VARCHAR(50) DEFAULT 'ventas',
    fecha_ingesta TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS usuarios_raw (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    fuente VARCHAR(50) DEFAULT 'usuarios',
    fecha_ingesta TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inventario_raw (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    fuente VARCHAR(50) DEFAULT 'inventario',
    fecha_ingesta TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS arriendos_raw (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    fuente VARCHAR(50) DEFAULT 'arriendos',
    fecha_ingesta TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bicicletas_raw (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    fuente VARCHAR(50) DEFAULT 'bicicletas',
    fecha_ingesta TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS despachos_raw (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    fuente VARCHAR(50) DEFAULT 'despachos',
    fecha_ingesta TIMESTAMP DEFAULT NOW()
);

-- Índices para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_ventas_raw_run_id ON ventas_raw(run_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_raw_run_id ON usuarios_raw(run_id);
CREATE INDEX IF NOT EXISTS idx_inventario_raw_run_id ON inventario_raw(run_id);
CREATE INDEX IF NOT EXISTS idx_arriendos_raw_run_id ON arriendos_raw(run_id);
CREATE INDEX IF NOT EXISTS idx_bicicletas_raw_run_id ON bicicletas_raw(run_id);
CREATE INDEX IF NOT EXISTS idx_despachos_raw_run_id ON despachos_raw(run_id);
