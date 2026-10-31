-- Inicialización de base de datos MasterBike Data Pipeline
-- Este script crea la estructura base. Las tablas se crean via SQLAlchemy al iniciar la app.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

COMMENT ON DATABASE portfolio_pipeline IS 'MasterBike Data Pipeline - ETL Platform';
