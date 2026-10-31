-- ============================================================
-- TABLAS CLEAN: Datos validados y transformados
-- ============================================================

CREATE TABLE IF NOT EXISTS ventas_clean (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    data_original JSONB,
    fuente VARCHAR(50) DEFAULT 'ventas',
    fecha_ingesta TIMESTAMP DEFAULT NOW(),
    transformaciones_aplicadas JSONB,
    estado_calidad VARCHAR(50) DEFAULT 'VALID'
);

CREATE TABLE IF NOT EXISTS usuarios_clean (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    data_original JSONB,
    fuente VARCHAR(50) DEFAULT 'usuarios',
    fecha_ingesta TIMESTAMP DEFAULT NOW(),
    transformaciones_aplicadas JSONB,
    estado_calidad VARCHAR(50) DEFAULT 'VALID'
);

CREATE TABLE IF NOT EXISTS inventario_clean (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    data_original JSONB,
    fuente VARCHAR(50) DEFAULT 'inventario',
    fecha_ingesta TIMESTAMP DEFAULT NOW(),
    transformaciones_aplicadas JSONB,
    estado_calidad VARCHAR(50) DEFAULT 'VALID'
);

CREATE TABLE IF NOT EXISTS arriendos_clean (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    data_original JSONB,
    fuente VARCHAR(50) DEFAULT 'arriendos',
    fecha_ingesta TIMESTAMP DEFAULT NOW(),
    transformaciones_aplicadas JSONB,
    estado_calidad VARCHAR(50) DEFAULT 'VALID'
);

CREATE TABLE IF NOT EXISTS bicicletas_clean (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    data_original JSONB,
    fuente VARCHAR(50) DEFAULT 'bicicletas',
    fecha_ingesta TIMESTAMP DEFAULT NOW(),
    transformaciones_aplicadas JSONB,
    estado_calidad VARCHAR(50) DEFAULT 'VALID'
);

CREATE TABLE IF NOT EXISTS despachos_clean (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    registro_id VARCHAR(100),
    data JSONB NOT NULL,
    data_original JSONB,
    fuente VARCHAR(50) DEFAULT 'despachos',
    fecha_ingesta TIMESTAMP DEFAULT NOW(),
    transformaciones_aplicadas JSONB,
    estado_calidad VARCHAR(50) DEFAULT 'VALID'
);

CREATE INDEX IF NOT EXISTS idx_ventas_clean_run_id ON ventas_clean(run_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_clean_run_id ON usuarios_clean(run_id);
CREATE INDEX IF NOT EXISTS idx_inventario_clean_run_id ON inventario_clean(run_id);
CREATE INDEX IF NOT EXISTS idx_arriendos_clean_run_id ON arriendos_clean(run_id);
CREATE INDEX IF NOT EXISTS idx_bicicletas_clean_run_id ON bicicletas_clean(run_id);
CREATE INDEX IF NOT EXISTS idx_despachos_clean_run_id ON despachos_clean(run_id);
