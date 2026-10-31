import json
import os
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

MOCK_DATA_PATH = os.getenv("MOCK_DATA_PATH", "./mock_data")

SOURCES = ["ventas", "usuarios", "inventario", "arriendos", "bicicletas", "despachos"]


class IngestionStage:
    """Lee datos desde los archivos mock que simulan los microservicios de MasterBike."""

    def ingest(self, source: str) -> List[Dict[str, Any]]:
        if source not in SOURCES:
            raise ValueError(f"Fuente desconocida: '{source}'. Fuentes válidas: {SOURCES}")

        file_path = os.path.join(MOCK_DATA_PATH, f"{source}.json")
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"Archivo de datos no encontrado: {file_path}"
            )

        with open(file_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        if not isinstance(records, list):
            raise ValueError(f"El archivo {file_path} debe contener un array JSON")

        logger.info(f"[INGESTION] Leídos {len(records)} registros desde {file_path}")
        return records

    def get_source_info(self, source: str) -> Dict:
        file_path = os.path.join(MOCK_DATA_PATH, f"{source}.json")
        return {
            "fuente": source,
            "archivo": file_path,
            "existe": os.path.exists(file_path),
        }

    def list_sources(self) -> List[Dict]:
        return [self.get_source_info(s) for s in SOURCES]
