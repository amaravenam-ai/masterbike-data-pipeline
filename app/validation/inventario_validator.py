from typing import Dict
from app.validation.base_validator import BaseValidator, ValidationResult

CATEGORIAS_VALIDAS = ["Repuesto", "Accesorio", "Equipamiento"]


class InventarioValidator(BaseValidator):
    """Valida registros del módulo Inventario de MasterBike."""

    def validate(self, record: Dict) -> ValidationResult:
        errors = []

        # ID producto
        errors += self._check_positive_int(record.get("id"), "id")

        # Nombre del producto: obligatorio, no vacío
        nombre = record.get("nombre_producto")
        if nombre is None:
            errors.append("Campo 'nombre_producto' es nulo")
        elif str(nombre).strip() == "":
            errors.append("Campo 'nombre_producto' está vacío")
        else:
            errors += self._check_max_length(nombre, "nombre_producto", 150)

        # Categoría: debe ser Repuesto, Accesorio o Equipamiento
        errors += self._check_enum(record.get("categoria"), "categoria", CATEGORIAS_VALIDAS)

        # Stock: no puede ser negativo
        errors += self._check_non_negative_int(record.get("stock"), "stock")

        # Stock mínimo: debe ser positivo
        errors += self._check_positive_int(record.get("stock_minimo"), "stock_minimo")

        return ValidationResult(record, len(errors) == 0, errors)
