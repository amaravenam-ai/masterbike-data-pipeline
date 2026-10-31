from typing import Dict
from app.transformations.base_transformer import BaseTransformer, TransformationResult


class VentasTransformer(BaseTransformer):
    """Transforma y limpia registros del módulo Ventas."""

    def transform(self, record: Dict) -> TransformationResult:
        data = self._copy(record)
        transformations = []

        # Normalizar estado a mayúsculas
        transformations += self._normalize_uppercase(data, ["estado"])

        # Redondear total a 2 decimales
        transformations += self._round_decimal(data, "total", 2)

        # Asegurar tipos correctos
        transformations += self._cast_to_int(data, "id")
        transformations += self._cast_to_int(data, "id_cliente")
        transformations += self._cast_to_float(data, "total")

        # Normalizar fecha
        if "fecha_venta" in data and data["fecha_venta"]:
            transformations.append("normalize_date:fecha_venta")

        return TransformationResult(record, data, transformations)
