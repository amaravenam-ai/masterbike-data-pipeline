"""Pruebas reales opt-in; no reutilizan ni eliminan tablas existentes."""
import json
import os
import uuid
from pathlib import Path
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

URL = os.getenv('PORTFOLIO_TEST_DATABASE_URL')
pytestmark = pytest.mark.skipif(not URL, reason='Requiere PostgreSQL aislado: PORTFOLIO_TEST_DATABASE_URL')


@pytest.fixture
def session(monkeypatch):
    url = make_url(URL)
    if url.host not in {'127.0.0.1', 'localhost', 'postgres'} or not url.database.startswith('portfolio_'):
        pytest.fail('Solo se permite una base local con prefijo portfolio_')
    schema = 'portfolio_test_' + uuid.uuid4().hex
    admin = create_engine(URL)
    with admin.begin() as c:
        c.execute(text(f'CREATE SCHEMA {schema}'))
    engine = create_engine(URL, connect_args={'options': f'-csearch_path={schema}'})
    from app.database.connection import Base
    import app.models.pipeline_models
    Base.metadata.create_all(engine)
    import app.pipeline.ingestion as ingestion
    monkeypatch.setattr(ingestion, 'MOCK_DATA_PATH', str(Path(__file__).resolve().parents[2]/'mock_data'))
    try:
        with Session(engine) as db:
            yield db
    finally:
        engine.dispose()
        with admin.begin() as c:
            c.execute(text(f'DROP SCHEMA {schema} CASCADE'))
        admin.dispose()


@pytest.mark.parametrize('source', ['ventas','usuarios','inventario','arriendos','bicicletas','despachos'])
def test_counts_and_repeated_run_are_persisted(session, source):
    from app.pipeline.orchestrator import PipelineOrchestrator
    from app.pipeline.loader import MODEL_MAP
    orchestrator = PipelineOrchestrator(session)
    a = orchestrator.run(source)
    assert a.estado == 'COMPLETED'
    assert a.total_registros == a.registros_validos + a.registros_error
    raw, clean, errors = MODEL_MAP[source]
    assert session.query(raw).filter_by(run_id=a.run_id).count() == a.total_registros
    assert session.query(clean).filter_by(run_id=a.run_id).count() == a.registros_validos
    assert session.query(errors).filter_by(run_id=a.run_id).count() == a.registros_error
    b = orchestrator.run(source)
    assert b.estado == 'COMPLETED' and b.run_id != a.run_id
    assert session.query(raw).count() == 2*a.total_registros


def test_empty_source_completes_without_rows(session, tmp_path, monkeypatch):
    from app.pipeline.orchestrator import PipelineOrchestrator
    (tmp_path/'ventas.json').write_text('[]', encoding='utf-8')
    import app.pipeline.ingestion as ingestion
    monkeypatch.setattr(ingestion, 'MOCK_DATA_PATH', str(tmp_path))
    result = PipelineOrchestrator(session).run('ventas')
    assert result.estado == 'COMPLETED'
    assert result.total_registros == result.registros_validos == result.registros_error == 0


@pytest.mark.parametrize('contents', [None, '{invalid-json', '{}'])
def test_unreadable_source_records_failure(session, tmp_path, monkeypatch, contents):
    from app.pipeline.orchestrator import PipelineOrchestrator
    from app.models.pipeline_models import PipelineRun
    import app.pipeline.ingestion as ingestion
    monkeypatch.setattr(ingestion, 'MOCK_DATA_PATH', str(tmp_path))
    if contents is not None:
        (tmp_path/'ventas.json').write_text(contents, encoding='utf-8')
    result = PipelineOrchestrator(session).run('ventas')
    assert result.estado == 'FAILED'
    stored = session.get(PipelineRun, result.run_id)
    assert stored.estado == 'FAILED' and stored.error_mensaje
    assert stored.fecha_fin is not None


def test_dashboard_uses_persisted_counts_even_when_zero(session):
    from app.pipeline.orchestrator import PipelineOrchestrator
    from app.pipeline.loader import MODEL_MAP
    from app.main import get_pipeline_status_detail
    result = PipelineOrchestrator(session).run('ventas')
    assert result.estado == 'COMPLETED' and result.registros_validos > 0
    status = get_pipeline_status_detail(source='ventas', db=session)
    assert status['run_id'] == str(result.run_id)
    assert status['registros_procesados'] == result.total_registros
    assert status['registros_validos'] == result.registros_validos
    assert status['registros_error'] == result.registros_error
    _, clean, _ = MODEL_MAP['ventas']
    session.query(clean).filter_by(run_id=result.run_id).delete()
    session.commit()
    status = get_pipeline_status_detail(source='ventas', db=session)
    assert status['registros_validos'] == 0
