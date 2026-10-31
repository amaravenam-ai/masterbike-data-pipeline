"""Tests de transformación para cada módulo del pipeline MasterBike."""
import pytest
from app.transformations.ventas_transformer import VentasTransformer
from app.transformations.usuarios_transformer import UsuariosTransformer
from app.transformations.inventario_transformer import InventarioTransformer
from app.transformations.arriendos_transformer import ArriendosTransformer
from app.transformations.bicicletas_transformer import BicicletasTransformer
from app.transformations.despachos_transformer import DespachosTransformer


class TestVentasTransformer:
    transformer = VentasTransformer()

    def test_normaliza_estado_a_mayusculas(self):
        result = self.transformer.transform({"id": 1, "id_cliente": 1, "fecha_venta": "2026-04-20", "total": 45990.00, "estado": "pagada"})
        assert result.transformed["estado"] == "PAGADA"
        assert "normalize_uppercase:estado" in result.transformations

    def test_redondea_total(self):
        result = self.transformer.transform({"id": 1, "id_cliente": 1, "fecha_venta": "2026-04-20", "total": 45990.555555, "estado": "PAGADA"})
        assert result.transformed["total"] == 45990.56

    def test_no_modifica_datos_originales(self):
        original = {"id": 1, "id_cliente": 1, "fecha_venta": "2026-04-20", "total": 100.0, "estado": "pendiente"}
        result = self.transformer.transform(original)
        assert result.original["estado"] == "pendiente"
        assert result.transformed["estado"] == "PENDIENTE"


class TestUsuariosTransformer:
    transformer = UsuariosTransformer()

    def test_normaliza_nombre_a_titlecase(self):
        result = self.transformer.transform({"id": 1, "nombre": "ARIEL ARAVENA", "correo": "ARIEL@TEST.CL", "rol": "administrador"})
        assert result.transformed["nombre"] == "Ariel Aravena"
        assert result.transformed["correo"] == "ariel@test.cl"
        assert result.transformed["rol"] == "ADMINISTRADOR"

    def test_trim_nombre(self):
        result = self.transformer.transform({"id": 2, "nombre": "  Brian Lizama  ", "correo": "b@b.cl", "rol": "VENDEDOR"})
        assert result.transformed["nombre"] == "Brian Lizama"


class TestInventarioTransformer:
    transformer = InventarioTransformer()

    def test_calcula_estado_stock_normal(self):
        result = self.transformer.transform({"id": 1, "nombre_producto": "Cadena", "categoria": "repuesto", "stock": 20, "stock_minimo": 5})
        assert result.transformed["estado_stock"] == "NORMAL"
        assert "calculate:estado_stock" in result.transformations

    def test_calcula_estado_stock_critico(self):
        result = self.transformer.transform({"id": 2, "nombre_producto": "Guantes", "categoria": "Accesorio", "stock": 3, "stock_minimo": 5})
        assert result.transformed["estado_stock"] == "CRITICO"

    def test_calcula_estado_stock_agotado(self):
        result = self.transformer.transform({"id": 3, "nombre_producto": "Luz", "categoria": "Accesorio", "stock": 0, "stock_minimo": 3})
        assert result.transformed["estado_stock"] == "AGOTADO"

    def test_normaliza_nombre_a_titlecase(self):
        result = self.transformer.transform({"id": 4, "nombre_producto": "CADENA SHIMANO", "categoria": "repuesto", "stock": 10, "stock_minimo": 3})
        assert result.transformed["nombre_producto"] == "Cadena Shimano"


class TestArriendosTransformer:
    transformer = ArriendosTransformer()

    def test_calcula_duracion_dias(self):
        result = self.transformer.transform({
            "id": 1, "id_cliente": 1, "id_bicicleta": 1,
            "fecha_inicio": "2026-04-22", "fecha_fin": "2026-04-24",
            "costo": 36000.00
        })
        assert result.transformed["duracion_dias"] == 3
        assert "calculate:duracion_dias" in result.transformations

    def test_duracion_mismo_dia(self):
        result = self.transformer.transform({
            "id": 2, "id_cliente": 1, "id_bicicleta": 1,
            "fecha_inicio": "2026-04-22", "fecha_fin": "2026-04-22",
            "costo": 12000.00
        })
        assert result.transformed["duracion_dias"] == 1


class TestBicicletasTransformer:
    transformer = BicicletasTransformer()

    def test_normaliza_codigo_a_mayusculas(self):
        result = self.transformer.transform({"id": 1, "codigo": "mb-mtb-004", "tipo": "montana", "estado": "disponible", "tarifa_hora": 4800.00})
        assert result.transformed["codigo"] == "MB-MTB-004"
        assert result.transformed["estado"] == "DISPONIBLE"

    def test_normaliza_tipo_a_titlecase(self):
        result = self.transformer.transform({"id": 2, "codigo": "MB-MTB-002", "tipo": "MONTANA", "estado": "DISPONIBLE", "tarifa_hora": 4500.00})
        assert result.transformed["tipo"] == "Montana"


class TestDespachosTransformer:
    transformer = DespachosTransformer()

    def test_normaliza_estado_a_mayusculas(self):
        result = self.transformer.transform({"id": 1, "id_venta": 1, "direccion": "Calle 123", "estado": "en_ruta", "fecha_estimada": "2026-04-25"})
        assert result.transformed["estado"] == "EN_RUTA"

    def test_limpia_espacios_direccion(self):
        result = self.transformer.transform({"id": 2, "id_venta": 2, "direccion": "  Av. Italia 250  ", "estado": "PENDIENTE", "fecha_estimada": "2026-04-26"})
        assert result.transformed["direccion"] == "Av. Italia 250"
        assert "strip_whitespace:direccion" in result.transformations
