from typing import Dict
from app.validation.base_validator import BaseValidator, ValidationResult

ESTADOS_VALIDOS = ["PAGADA", "PENDIENTE", "CANCELADA"]


class VentasValidator(BaseValidator):
    """Valida registros del módulo Ventas de MasterBike."""

    def validate(self, record: Dict) -> ValidationResult:
        errors = []

        # ID de venta
        errors += self._check_positive_int(record.get("id"), "id")

        # ID cliente: referencia a módulo Clientes
        errors += self._check_positive_int(record.get("id_cliente"), "id_cliente")

        # Fecha de venta
        errors += self._check_valid_date(record.get("fecha_venta"), "fecha_venta")

        # Total: debe ser positivo (precio mínimo $1)
        total = record.get("total")
        if total is not None:
            try:
                t = float(total)
                if t <= 0:
                    errors.append(f"Campo 'total' debe ser mayor a 0, valor: {total}")
            except (TypeError, ValueError):
                errors.append(f"Campo 'total' debe ser numérico, valor: '{total}'")
        else:
            errors.append("Campo 'total' es nulo")

        # Estado del pago
        errors += self._check_enum(record.get("estado"), "estado", ESTADOS_VALIDOS)

        return ValidationResult(record, len(errors) == 0, errors)
