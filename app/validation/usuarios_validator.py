from typing import Dict
from app.validation.base_validator import BaseValidator, ValidationResult

ROLES_VALIDOS = ["ADMINISTRADOR", "TECNICO", "VENDEDOR"]


class UsuariosValidator(BaseValidator):
    """Valida registros del módulo Usuarios de MasterBike."""

    def validate(self, record: Dict) -> ValidationResult:
        errors = []

        # ID usuario
        errors += self._check_positive_int(record.get("id"), "id")

        # Nombre: obligatorio, no vacío, máx 100 chars
        nombre = record.get("nombre")
        if nombre is None:
            errors.append("Campo 'nombre' es nulo")
        elif str(nombre).strip() == "":
            errors.append("Campo 'nombre' está vacío")
        else:
            errors += self._check_max_length(nombre, "nombre", 100)

        # Correo: formato email válido
        errors += self._check_email(record.get("correo"), "correo")

        # Rol: debe ser uno de los roles del sistema
        errors += self._check_enum(record.get("rol"), "rol", ROLES_VALIDOS)

        return ValidationResult(record, len(errors) == 0, errors)
