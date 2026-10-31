from typing import Dict
from datetime import datetime
from app.validation.base_validator import BaseValidator, ValidationResult


class ArriendosValidator(BaseValidator):
    """Valida registros del módulo Arriendos de MasterBike."""

    def validate(self, record: Dict) -> ValidationResult:
        errors = []

        # ID arriendo
        errors += self._check_positive_int(record.get("id"), "id")

        # ID cliente
        errors += self._check_positive_int(record.get("id_cliente"), "id_cliente")

        # ID bicicleta
        errors += self._check_positive_int(record.get("id_bicicleta"), "id_bicicleta")

        # Fecha inicio
        errors += self._check_valid_date(record.get("fecha_inicio"), "fecha_inicio")

        # Fecha fin
        errors += self._check_valid_date(record.get("fecha_fin"), "fecha_fin")

        # Validar que fecha_fin >= fecha_inicio
        fi = record.get("fecha_inicio")
        ff = record.get("fecha_fin")
        if fi and ff and isinstance(fi, str) and isinstance(ff, str):
            try:
                d_inicio = datetime.strptime(fi, "%Y-%m-%d")
                d_fin = datetime.strptime(ff, "%Y-%m-%d")
                if d_fin < d_inicio:
                    errors.append(
                        f"'fecha_fin' ({ff}) no puede ser anterior a 'fecha_inicio' ({fi})"
                    )
            except ValueError:
                pass  # ya detectado en check_valid_date

        # Costo: debe ser positivo
        errors += self._check_positive_decimal(record.get("costo"), "costo")

        return ValidationResult(record, len(errors) == 0, errors)
