import re
from datetime import datetime
from typing import Any, Dict, List, Tuple


class ValidationResult:
    """Resultado de validar un único registro."""

    def __init__(self, record: Dict, is_valid: bool, errors: List[str]):
        self.record = record
        self.is_valid = is_valid
        self.errors = errors


class BaseValidator:
    """Clase base con utilidades comunes de validación."""

    REQUIRED_FIELDS: List[str] = []

    def validate(self, record: Dict) -> ValidationResult:
        raise NotImplementedError

    def _check_required(self, record: Dict, fields: List[str]) -> List[str]:
        errors = []
        for field in fields:
            value = record.get(field)
            if value is None:
                errors.append(f"Campo '{field}' es nulo o no existe")
            elif isinstance(value, str) and value.strip() == "":
                errors.append(f"Campo '{field}' está vacío")
        return errors

    def _check_positive_int(self, value: Any, field: str) -> List[str]:
        if value is None:
            return [f"Campo '{field}' es nulo"]
        try:
            v = int(value)
            if v <= 0:
                return [f"Campo '{field}' debe ser un entero positivo, valor: {value}"]
        except (TypeError, ValueError):
            return [f"Campo '{field}' debe ser numérico, valor: '{value}'"]
        return []

    def _check_positive_decimal(self, value: Any, field: str) -> List[str]:
        if value is None:
            return [f"Campo '{field}' es nulo"]
        try:
            v = float(value)
            if v <= 0:
                return [f"Campo '{field}' debe ser mayor a 0, valor: {value}"]
        except (TypeError, ValueError):
            return [f"Campo '{field}' debe ser numérico, valor: '{value}'"]
        return []

    def _check_non_negative_int(self, value: Any, field: str) -> List[str]:
        if value is None:
            return [f"Campo '{field}' es nulo"]
        try:
            v = int(value)
            if v < 0:
                return [f"Campo '{field}' no puede ser negativo, valor: {value}"]
        except (TypeError, ValueError):
            return [f"Campo '{field}' debe ser numérico entero, valor: '{value}'"]
        return []

    def _check_valid_date(self, value: Any, field: str) -> List[str]:
        if value is None:
            return [f"Campo '{field}' es nulo"]
        if isinstance(value, str):
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return [f"Campo '{field}' no tiene formato de fecha válido (YYYY-MM-DD), valor: '{value}'"]
        return []

    def _check_enum(self, value: Any, field: str, allowed: List[str]) -> List[str]:
        if value is None:
            return [f"Campo '{field}' es nulo"]
        normalized = str(value).upper().strip()
        if normalized not in [a.upper() for a in allowed]:
            return [f"Campo '{field}' tiene valor inválido '{value}'. Valores permitidos: {allowed}"]
        return []

    def _check_email(self, value: Any, field: str) -> List[str]:
        if value is None:
            return [f"Campo '{field}' es nulo"]
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, str(value).strip()):
            return [f"Campo '{field}' no tiene formato de email válido, valor: '{value}'"]
        return []

    def _check_max_length(self, value: Any, field: str, max_len: int) -> List[str]:
        if value is not None and len(str(value)) > max_len:
            return [f"Campo '{field}' excede {max_len} caracteres"]
        return []


def validate_batch(
    records: List[Dict], validator: BaseValidator
) -> Tuple[List[Dict], List[Dict]]:
    """Valida un lote de registros y retorna (válidos, errores)."""
    valid_records = []
    error_records = []
    for record in records:
        result = validator.validate(record)
        if result.is_valid:
            valid_records.append(record)
        else:
            error_records.append({
                **record,
                "_errores_detectados": result.errors,
            })
    return valid_records, error_records
