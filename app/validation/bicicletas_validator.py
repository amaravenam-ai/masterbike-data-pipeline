import re
from typing import Dict
from app.validation.base_validator import BaseValidator, ValidationResult

TIPOS_VALIDOS = ["Montana", "Ruta", "Urbana"]
ESTADOS_VALIDOS = ["DISPONIBLE", "MANTENCION", "ARRENDADA"]
CODIGO_PATTERN = re.compile(r"^MB-[A-Z]{3}-\d{3}$")


class BicicletasValidator(BaseValidator):
    """Valida registros del módulo Bicicletas de MasterBike."""

    def validate(self, record: Dict) -> ValidationResult:
        errors = []

        # ID bicicleta
        errors += self._check_positive_int(record.get("id"), "id")

        # Código único: formato MB-XXX-NNN
        codigo = record.get("codigo")
        if codigo is None:
            errors.append("Campo 'codigo' es nulo")
        else:
            normalized = str(codigo).upper().strip()
            if not CODIGO_PATTERN.match(normalized):
                errors.append(
                    f"Campo 'codigo' no tiene el formato requerido MB-XXX-NNN, valor: '{codigo}'"
                )

        # Tipo de bicicleta
        errors += self._check_enum(record.get("tipo"), "tipo", TIPOS_VALIDOS)

        # Estado de la bicicleta
        errors += self._check_enum(record.get("estado"), "estado", ESTADOS_VALIDOS)

        # Tarifa por hora: debe ser positiva
        errors += self._check_positive_decimal(record.get("tarifa_hora"), "tarifa_hora")

        return ValidationResult(record, len(errors) == 0, errors)
