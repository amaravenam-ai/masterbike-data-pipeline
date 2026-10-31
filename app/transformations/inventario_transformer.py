from typing import Dict
from app.transformations.base_transformer import BaseTransformer, TransformationResult


class InventarioTransformer(BaseTransformer):
    """Transforma y limpia registros del módulo Inventario."""

    def transform(self, record: Dict) -> TransformationResult:
        data = self._copy(record)
        transformations = []

        # Normalizar nombre a Title Case
        transformations += self._normalize_titlecase(data, ["nombre_producto"])

        # Normalizar categoría a Title Case
        transformations += self._normalize_titlecase(data, ["categoria"])

        # Asegurar tipos enteros
        transformations += self._cast_to_int(data, "id")
        transformations += self._cast_to_int(data, "stock")
        transformations += self._cast_to_int(data, "stock_minimo")

        # Calcular estado de stock (campo derivado)
        stock = data.get("stock", 0)
        stock_min = data.get("stock_minimo", 0)
        if isinstance(stock, int) and isinstance(stock_min, int):
            if stock == 0:
                data["estado_stock"] = "AGOTADO"
            elif stock <= stock_min:
                data["estado_stock"] = "CRITICO"
            elif stock <= stock_min * 2:
                data["estado_stock"] = "BAJO"
            else:
                data["estado_stock"] = "NORMAL"
            transformations.append("calculate:estado_stock")

        return TransformationResult(record, data, transformations)
