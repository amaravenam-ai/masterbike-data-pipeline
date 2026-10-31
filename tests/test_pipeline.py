"""Tests del pipeline ETL completo (sin base de datos)."""
import pytest
from unittest.mock import MagicMock, patch
from app.pipeline.ingestion import IngestionStage, SOURCES
from app.pipeline.validation_stage import ValidationStage
from app.pipeline.transformation_stage import TransformationStage


class TestIngestionStage:
    ingestion = IngestionStage()

    def test_fuente_invalida(self):
        with pytest.raises(ValueError, match="Fuente desconocida"):
            self.ingestion.ingest("modulo_inexistente")

    def test_sources_disponibles(self):
        assert "ventas" in SOURCES
        assert "usuarios" in SOURCES
        assert "inventario" in SOURCES
        assert "arriendos" in SOURCES
        assert "bicicletas" in SOURCES
        assert "despachos" in SOURCES

    def test_list_sources_retorna_todas(self):
        sources = self.ingestion.list_sources()
        assert len(sources) == 6
        for s in sources:
            assert "fuente" in s
            assert "archivo" in s
            assert "existe" in s


class TestValidationStage:
    validation = ValidationStage()

    def test_fuente_invalida(self):
        with pytest.raises(ValueError, match="No existe validador"):
            self.validation.validate([], "fuente_invalida")

    def test_lote_vacio(self):
        valid, errors = self.validation.validate([], "ventas")
        assert valid == []
        assert errors == []

    def test_separa_validos_de_errores_ventas(self):
        records = [
            {"id": 1, "id_cliente": 1, "fecha_venta": "2026-04-20", "total": 45000.00, "estado": "PAGADA"},
            {"id": 2, "id_cliente": None, "fecha_venta": "2026-04-21", "total": 30000.00, "estado": "PAGADA"},
            {"id": 3, "id_cliente": 2, "fecha_venta": "fecha-mala", "total": 20000.00, "estado": "PAGADA"},
        ]
        valid, errors = self.validation.validate(records, "ventas")
        assert len(valid) == 1
        assert len(errors) == 2
        assert "_errores_detectados" in errors[0]

    def test_separa_validos_de_errores_usuarios(self):
        records = [
            {"id": 1, "nombre": "Ariel", "correo": "ariel@test.cl", "rol": "ADMINISTRADOR"},
            {"id": 2, "nombre": "", "correo": "test@test.cl", "rol": "VENDEDOR"},
        ]
        valid, errors = self.validation.validate(records, "usuarios")
        assert len(valid) == 1
        assert len(errors) == 1


class TestTransformationStage:
    transformation = TransformationStage()

    def test_fuente_invalida(self):
        with pytest.raises(ValueError, match="No existe transformer"):
            self.transformation.transform([], "fuente_invalida")

    def test_lote_vacio(self):
        result = self.transformation.transform([], "ventas")
        assert result == []

    def test_estructura_resultado(self):
        records = [
            {"id": 1, "id_cliente": 1, "fecha_venta": "2026-04-20", "total": 45990.555, "estado": "pagada"},
        ]
        result = self.transformation.transform(records, "ventas")
        assert len(result) == 1
        item = result[0]
        assert "data" in item
        assert "data_original" in item
        assert "transformaciones_aplicadas" in item
        assert item["data"]["estado"] == "PAGADA"
        assert item["data_original"]["estado"] == "pagada"

    def test_todas_las_fuentes_funcionan(self):
        test_data = {
            "ventas":     [{"id": 1, "id_cliente": 1, "fecha_venta": "2026-04-20", "total": 50000.0, "estado": "PAGADA"}],
            "usuarios":   [{"id": 1, "nombre": "test user", "correo": "t@t.cl", "rol": "VENDEDOR"}],
            "inventario": [{"id": 1, "nombre_producto": "item", "categoria": "Repuesto", "stock": 10, "stock_minimo": 2}],
            "arriendos":  [{"id": 1, "id_cliente": 1, "id_bicicleta": 1, "fecha_inicio": "2026-04-22", "fecha_fin": "2026-04-23", "costo": 18000.0}],
            "bicicletas": [{"id": 1, "codigo": "mb-mtb-001", "tipo": "montana", "estado": "disponible", "tarifa_hora": 4500.0}],
            "despachos":  [{"id": 1, "id_venta": 1, "direccion": "Calle 123", "estado": "en_ruta", "fecha_estimada": "2026-04-24"}],
        }
        for fuente, records in test_data.items():
            result = self.transformation.transform(records, fuente)
            assert len(result) == 1, f"Fallo en fuente: {fuente}"
