import logging
from typing import Any, Dict, List, Tuple

from app.validation.ventas_validator import VentasValidator
from app.validation.usuarios_validator import UsuariosValidator
from app.validation.inventario_validator import InventarioValidator
from app.validation.arriendos_validator import ArriendosValidator
from app.validation.bicicletas_validator import BicicletasValidator
from app.validation.despachos_validator import DespachosValidator
from app.validation.base_validator import BaseValidator

logger = logging.getLogger(__name__)

VALIDATORS: Dict[str, BaseValidator] = {
    "ventas": VentasValidator(),
    "usuarios": UsuariosValidator(),
    "inventario": InventarioValidator(),
    "arriendos": ArriendosValidator(),
    "bicicletas": BicicletasValidator(),
    "despachos": DespachosValidator(),
}


class ValidationStage:
    """Etapa de validación del pipeline: separa registros válidos de erróneos."""

    def validate(
        self, records: List[Dict], source: str
    ) -> Tuple[List[Dict], List[Dict]]:
        validator = VALIDATORS.get(source)
        if not validator:
            raise ValueError(f"No existe validador para la fuente: '{source}'")

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

        logger.info(
            f"[VALIDATION][{source.upper()}] "
            f"{len(valid_records)} válidos / {len(error_records)} con errores"
        )
        return valid_records, error_records
