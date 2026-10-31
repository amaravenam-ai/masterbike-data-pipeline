import logging
from typing import Dict, List

from app.transformations.ventas_transformer import VentasTransformer
from app.transformations.usuarios_transformer import UsuariosTransformer
from app.transformations.inventario_transformer import InventarioTransformer
from app.transformations.arriendos_transformer import ArriendosTransformer
from app.transformations.bicicletas_transformer import BicicletasTransformer
from app.transformations.despachos_transformer import DespachosTransformer
from app.transformations.base_transformer import BaseTransformer

logger = logging.getLogger(__name__)

TRANSFORMERS: Dict[str, BaseTransformer] = {
    "ventas": VentasTransformer(),
    "usuarios": UsuariosTransformer(),
    "inventario": InventarioTransformer(),
    "arriendos": ArriendosTransformer(),
    "bicicletas": BicicletasTransformer(),
    "despachos": DespachosTransformer(),
}


class TransformationStage:
    """Etapa de transformación: limpia y enriquece registros válidos."""

    def transform(self, records: List[Dict], source: str) -> List[Dict]:
        transformer = TRANSFORMERS.get(source)
        if not transformer:
            raise ValueError(f"No existe transformer para la fuente: '{source}'")

        transformed = []
        for record in records:
            result = transformer.transform(record)
            transformed.append({
                "data": result.transformed,
                "data_original": result.original,
                "transformaciones_aplicadas": result.transformations,
            })

        logger.info(
            f"[TRANSFORMATION][{source.upper()}] "
            f"{len(transformed)} registros transformados"
        )
        return transformed
