import copy
from typing import Any, Dict, List, Tuple


class TransformationResult:
    """Resultado de transformar un único registro."""

    def __init__(self, original: Dict, transformed: Dict, transformations: List[str]):
        self.original = original
        self.transformed = transformed
        self.transformations = transformations


class BaseTransformer:
    """Clase base con utilidades de transformación comunes."""

    def transform(self, record: Dict) -> TransformationResult:
        raise NotImplementedError

    def _copy(self, record: Dict) -> Dict:
        return copy.deepcopy(record)

    def _normalize_uppercase(self, data: Dict, fields: List[str]) -> List[str]:
        applied = []
        for field in fields:
            if field in data and data[field] is not None:
                original = data[field]
                data[field] = str(original).upper().strip()
                if data[field] != str(original):
                    applied.append(f"normalize_uppercase:{field}")
        return applied

    def _normalize_titlecase(self, data: Dict, fields: List[str]) -> List[str]:
        applied = []
        for field in fields:
            if field in data and data[field] is not None:
                original = data[field]
                data[field] = str(original).strip().title()
                if data[field] != str(original):
                    applied.append(f"normalize_titlecase:{field}")
        return applied

    def _normalize_lowercase(self, data: Dict, fields: List[str]) -> List[str]:
        applied = []
        for field in fields:
            if field in data and data[field] is not None:
                original = data[field]
                data[field] = str(original).lower().strip()
                if data[field] != str(original):
                    applied.append(f"normalize_lowercase:{field}")
        return applied

    def _round_decimal(self, data: Dict, field: str, decimals: int = 2) -> List[str]:
        applied = []
        if field in data and data[field] is not None:
            try:
                original = data[field]
                data[field] = round(float(original), decimals)
                applied.append(f"round_decimal:{field}:{decimals}")
            except (TypeError, ValueError):
                pass
        return applied

    def _strip_whitespace(self, data: Dict, fields: List[str]) -> List[str]:
        applied = []
        for field in fields:
            if field in data and isinstance(data[field], str):
                original = data[field]
                data[field] = data[field].strip()
                if data[field] != original:
                    applied.append(f"strip_whitespace:{field}")
        return applied

    def _cast_to_int(self, data: Dict, field: str) -> List[str]:
        if field in data and data[field] is not None:
            try:
                data[field] = int(data[field])
                return [f"cast_to_int:{field}"]
            except (TypeError, ValueError):
                pass
        return []

    def _cast_to_float(self, data: Dict, field: str) -> List[str]:
        if field in data and data[field] is not None:
            try:
                data[field] = float(data[field])
                return [f"cast_to_float:{field}"]
            except (TypeError, ValueError):
                pass
        return []


def transform_batch(records: List[Dict], transformer: BaseTransformer) -> List[TransformationResult]:
    return [transformer.transform(record) for record in records]
