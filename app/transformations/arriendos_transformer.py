from typing import Dict
from datetime import datetime
from app.transformations.base_transformer import BaseTransformer, TransformationResult


class ArriendosTransformer(BaseTransformer):
    """Transforma y limpia registros del módulo Arriendos."""

    def transform(self, record: Dict) -> TransformationResult:
        data = self._copy(record)
        transformations = []

        # Asegurar tipos correctos
        transformations += self._cast_to_int(data, "id")
        transformations += self._cast_to_int(data, "id_cliente")
        transformations += self._cast_to_int(data, "id_bicicleta")
        transformations += self._round_decimal(data, "costo", 2)
        transformations += self._cast_to_float(data, "costo")

        # Calcular duración en días (campo derivado)
        fi = data.get("fecha_inicio")
        ff = data.get("fecha_fin")
        if fi and ff:
            try:
                d_inicio = datetime.strptime(str(fi), "%Y-%m-%d")
                d_fin = datetime.strptime(str(ff), "%Y-%m-%d")
                duracion = (d_fin - d_inicio).days + 1  # inclusivo
                data["duracion_dias"] = max(duracion, 1)
                transformations.append("calculate:duracion_dias")
            except ValueError:
                pass

        return TransformationResult(record, data, transformations)
