"""Tests de validación para cada módulo del pipeline MasterBike."""
import pytest
from app.validation.ventas_validator import VentasValidator
from app.validation.usuarios_validator import UsuariosValidator
from app.validation.inventario_validator import InventarioValidator
from app.validation.arriendos_validator import ArriendosValidator
from app.validation.bicicletas_validator import BicicletasValidator
from app.validation.despachos_validator import DespachosValidator


# ── Ventas ───────────────────────────────────────────────────
class TestVentasValidator:
    validator = VentasValidator()

    def test_registro_valido(self):
        record = {"id": 1, "id_cliente": 1, "fecha_venta": "2026-04-20", "total": 45990.00, "estado": "PAGADA"}
        result = self.validator.validate(record)
        assert result.is_valid is True
        assert result.errors == []

    def test_estado_en_minusculas_es_valido(self):
        record = {"id": 2, "id_cliente": 2, "fecha_venta": "2026-04-21", "total": 10000.00, "estado": "pagada"}
        result = self.validator.validate(record)
        assert result.is_valid is True

    def test_id_cliente_nulo(self):
        record = {"id": 3, "id_cliente": None, "fecha_venta": "2026-04-22", "total": 30000.00, "estado": "PAGADA"}
        result = self.validator.validate(record)
        assert result.is_valid is False
        assert any("id_cliente" in e for e in result.errors)

    def test_fecha_invalida(self):
        record = {"id": 4, "id_cliente": 1, "fecha_venta": "fecha-invalida", "total": 30000.00, "estado": "PAGADA"}
        result = self.validator.validate(record)
        assert result.is_valid is False
        assert any("fecha_venta" in e for e in result.errors)

    def test_total_negativo(self):
        record = {"id": 5, "id_cliente": 1, "fecha_venta": "2026-04-22", "total": -500.00, "estado": "PAGADA"}
        result = self.validator.validate(record)
        assert result.is_valid is False
        assert any("total" in e for e in result.errors)

    def test_total_cero(self):
        record = {"id": 6, "id_cliente": 1, "fecha_venta": "2026-04-22", "total": 0.00, "estado": "PAGADA"}
        result = self.validator.validate(record)
        assert result.is_valid is False

    def test_estado_invalido(self):
        record = {"id": 7, "id_cliente": 1, "fecha_venta": "2026-04-22", "total": 50000.00, "estado": "ESTADO_RARO"}
        result = self.validator.validate(record)
        assert result.is_valid is False
        assert any("estado" in e for e in result.errors)


# ── Usuarios ─────────────────────────────────────────────────
class TestUsuariosValidator:
    validator = UsuariosValidator()

    def test_registro_valido(self):
        record = {"id": 1, "nombre": "Ariel Aravena", "correo": "ariel@masterbikes.cl", "rol": "ADMINISTRADOR"}
        result = self.validator.validate(record)
        assert result.is_valid is True

    def test_correo_invalido(self):
        record = {"id": 2, "nombre": "Felipe Torres", "correo": "correo-invalido", "rol": "TECNICO"}
        result = self.validator.validate(record)
        assert result.is_valid is False
        assert any("correo" in e for e in result.errors)

    def test_nombre_vacio(self):
        record = {"id": 3, "nombre": "", "correo": "test@masterbikes.cl", "rol": "VENDEDOR"}
        result = self.validator.validate(record)
        assert result.is_valid is False
        assert any("nombre" in e for e in result.errors)

    def test_rol_invalido(self):
        record = {"id": 4, "nombre": "Test User", "correo": "test@masterbikes.cl", "rol": "GERENTE"}
        result = self.validator.validate(record)
        assert result.is_valid is False

    def test_id_nulo(self):
        record = {"id": None, "nombre": "Test", "correo": "t@t.cl", "rol": "VENDEDOR"}
        result = self.validator.validate(record)
        assert result.is_valid is False


# ── Inventario ───────────────────────────────────────────────
class TestInventarioValidator:
    validator = InventarioValidator()

    def test_registro_valido(self):
        record = {"id": 1, "nombre_producto": "Cadena Shimano 10V", "categoria": "Repuesto", "stock": 20, "stock_minimo": 5}
        result = self.validator.validate(record)
        assert result.is_valid is True

    def test_stock_negativo(self):
        record = {"id": 2, "nombre_producto": "Llanta", "categoria": "Repuesto", "stock": -5, "stock_minimo": 3}
        result = self.validator.validate(record)
        assert result.is_valid is False
        assert any("stock" in e for e in result.errors)

    def test_categoria_invalida(self):
        record = {"id": 3, "nombre_producto": "Item", "categoria": "INVALIDA", "stock": 10, "stock_minimo": 2}
        result = self.validator.validate(record)
        assert result.is_valid is False

    def test_nombre_vacio(self):
        record = {"id": 4, "nombre_producto": "", "categoria": "Repuesto", "stock": 10, "stock_minimo": 2}
        result = self.validator.validate(record)
        assert result.is_valid is False

    def test_stock_cero_es_valido(self):
        record = {"id": 5, "nombre_producto": "Luz LED", "categoria": "Accesorio", "stock": 0, "stock_minimo": 3}
        result = self.validator.validate(record)
        assert result.is_valid is True


# ── Arriendos ────────────────────────────────────────────────
class TestArriendosValidator:
    validator = ArriendosValidator()

    def test_registro_valido(self):
        record = {"id": 1, "id_cliente": 1, "id_bicicleta": 1, "fecha_inicio": "2026-04-22", "fecha_fin": "2026-04-23", "costo": 18000.00}
        result = self.validator.validate(record)
        assert result.is_valid is True

    def test_fecha_fin_antes_de_inicio(self):
        record = {"id": 2, "id_cliente": 1, "id_bicicleta": 1, "fecha_inicio": "2026-04-22", "fecha_fin": "2026-04-20", "costo": 5000.00}
        result = self.validator.validate(record)
        assert result.is_valid is False
        assert any("fecha_fin" in e for e in result.errors)

    def test_costo_negativo(self):
        record = {"id": 3, "id_cliente": 1, "id_bicicleta": 1, "fecha_inicio": "2026-04-22", "fecha_fin": "2026-04-23", "costo": -100.00}
        result = self.validator.validate(record)
        assert result.is_valid is False

    def test_id_bicicleta_nulo(self):
        record = {"id": 4, "id_cliente": 1, "id_bicicleta": None, "fecha_inicio": "2026-04-22", "fecha_fin": "2026-04-23", "costo": 10000.00}
        result = self.validator.validate(record)
        assert result.is_valid is False


# ── Bicicletas ───────────────────────────────────────────────
class TestBicicletasValidator:
    validator = BicicletasValidator()

    def test_registro_valido(self):
        record = {"id": 1, "codigo": "MB-MTB-001", "tipo": "Montana", "estado": "DISPONIBLE", "tarifa_hora": 4500.00}
        result = self.validator.validate(record)
        assert result.is_valid is True

    def test_codigo_invalido(self):
        record = {"id": 2, "codigo": "CODIGO-MALO", "tipo": "Montana", "estado": "DISPONIBLE", "tarifa_hora": 4500.00}
        result = self.validator.validate(record)
        assert result.is_valid is False
        assert any("codigo" in e for e in result.errors)

    def test_tipo_invalido(self):
        record = {"id": 3, "codigo": "MB-MTB-003", "tipo": "Carretera", "estado": "DISPONIBLE", "tarifa_hora": 4500.00}
        result = self.validator.validate(record)
        assert result.is_valid is False

    def test_tarifa_negativa(self):
        record = {"id": 4, "codigo": "MB-URB-004", "tipo": "Urbana", "estado": "DISPONIBLE", "tarifa_hora": -100.00}
        result = self.validator.validate(record)
        assert result.is_valid is False


# ── Despachos ─────────────────────────────────────────────────
class TestDespachosValidator:
    validator = DespachosValidator()

    def test_registro_valido(self):
        record = {"id": 1, "id_venta": 1, "direccion": "Av. San Diego 123", "estado": "EN_PREPARACION", "fecha_estimada": "2026-04-24"}
        result = self.validator.validate(record)
        assert result.is_valid is True

    def test_direccion_vacia(self):
        record = {"id": 2, "id_venta": 1, "direccion": "", "estado": "EN_PREPARACION", "fecha_estimada": "2026-04-24"}
        result = self.validator.validate(record)
        assert result.is_valid is False

    def test_estado_invalido(self):
        record = {"id": 3, "id_venta": 1, "direccion": "Calle 123", "estado": "ENVIADO", "fecha_estimada": "2026-04-24"}
        result = self.validator.validate(record)
        assert result.is_valid is False

    def test_id_venta_nulo(self):
        record = {"id": 4, "id_venta": None, "direccion": "Calle 123", "estado": "PENDIENTE", "fecha_estimada": "2026-04-24"}
        result = self.validator.validate(record)
        assert result.is_valid is False
