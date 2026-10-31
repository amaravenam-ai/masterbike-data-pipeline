from typing import Dict
from app.validation.base_validator import BaseValidator, ValidationResult

ESTADOS_VALIDOS = ["EN_PREPARACION", "EN_RUTA", "PENDIENTE", "ENTREGADO"]


class DespachosValidator(BaseValidator):
    """Valida registros del módulo Despachos de MasterBike."""

    def validate(self, record: Dict) -> ValidationResult:
        errors = []

        # ID despacho
        errors += self._check_positive_int(record.get("id"), "id")

        # ID venta: referencia al módulo Ventas
        errors += self._check_positive_int(record.get("id_venta"), "id_venta")

        # Dirección: obligatoria, no vacía
        direccion = record.get("direccion")
        if direccion is None:
            errors.append("Campo 'direccion' es nulo")
        elif str(direccion).strip() == "":
            errors.append("Campo 'direccion' está vacío")
        else:
            errors += self._check_max_length(direccion, "direccion", 250)

        # Estado del despacho
        errors += self._check_enum(record.get("estado"), "estado", ESTADOS_VALIDOS)

        # Fecha estimada de entrega
        errors += self._check_valid_date(record.get("fecha_estimada"), "fecha_estimada")

        return ValidationResult(record, len(errors) == 0, errors)
