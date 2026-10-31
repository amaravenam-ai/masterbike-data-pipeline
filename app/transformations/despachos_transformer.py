from typing import Dict
from app.transformations.base_transformer import BaseTransformer, TransformationResult


class DespachosTransformer(BaseTransformer):
    """Transforma y limpia registros del módulo Despachos."""

    def transform(self, record: Dict) -> TransformationResult:
        data = self._copy(record)
        transformations = []

        # Normalizar estado a mayúsculas
        transformations += self._normalize_uppercase(data, ["estado"])

        # Limpiar espacios en dirección
        transformations += self._strip_whitespace(data, ["direccion"])

        # Asegurar tipos correctos
        transformations += self._cast_to_int(data, "id")
        transformations += self._cast_to_int(data, "id_venta")

        return TransformationResult(record, data, transformations)
