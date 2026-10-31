from typing import Dict
from app.transformations.base_transformer import BaseTransformer, TransformationResult


class UsuariosTransformer(BaseTransformer):
    """Transforma y limpia registros del módulo Usuarios."""

    def transform(self, record: Dict) -> TransformationResult:
        data = self._copy(record)
        transformations = []

        # Normalizar nombre a Title Case
        transformations += self._normalize_titlecase(data, ["nombre"])

        # Normalizar correo a minúsculas
        transformations += self._normalize_lowercase(data, ["correo"])

        # Normalizar rol a mayúsculas
        transformations += self._normalize_uppercase(data, ["rol"])

        # Asegurar tipo correcto para ID
        transformations += self._cast_to_int(data, "id")

        return TransformationResult(record, data, transformations)
