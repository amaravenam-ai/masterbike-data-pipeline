import os
import logging
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://portfolio@127.0.0.1:55437/portfolio_pipeline"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(attempts=15, delay=2):
    from app.models.pipeline_models import (  # noqa: F401
        PipelineRun,
        VentasRaw, VentasClean, VentasError,
        UsuariosRaw, UsuariosClean, UsuariosError,
        InventarioRaw, InventarioClean, InventarioError,
        ArriendosRaw, ArriendosClean, ArriendosError,
        BicicletasRaw, BicicletasClean, BicicletasError,
        DespachosRaw, DespachosClean, DespachosError,
    )
    for attempt in range(attempts):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Base de datos inicializada correctamente")
            return
        except OperationalError:
            if attempt + 1 == attempts:
                logger.error("Base no disponible tras agotar los intentos de arranque")
                raise
            logger.warning("Esperando PostgreSQL durante el arranque (%s/%s)", attempt + 1, attempts)
            time.sleep(delay)


def check_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return False
