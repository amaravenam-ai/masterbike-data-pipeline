from typing import Dict
from app.transformations.base_transformer import BaseTransformer, TransformationResult


class BicicletasTransformer(BaseTransformer):
    """Transforma y limpia registros del módulo Bicicletas."""

    def transform(self, record: Dict) -> TransformationResult:
        data = self._copy(record)
        transformations = []

        # Normalizar código a mayúsculas (MB-MTB-001 format)
        transformations += self._normalize_uppercase(data, ["codigo"])

        # Normalizar tipo a Title Case
        transformations += self._normalize_titlecase(data, ["tipo"])

        # Normalizar estado a mayúsculas
        transformations += self._normalize_uppercase(data, ["estado"])

        # Asegurar tipos correctos
        transformations += self._cast_to_int(data, "id")
        transformations += self._round_decimal(data, "tarifa_hora", 2)
        transformations += self._cast_to_float(data, "tarifa_hora")

        return TransformationResult(record, data, transformations)
