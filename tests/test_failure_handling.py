from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException
from app.pipeline.loader import LoaderStage
from app.api.routes.pipeline import run_pipeline


def test_failed_run_rolls_back_before_recording_failure():
    db = MagicMock()
    run = MagicMock()
    LoaderStage(db).fail_run(run, 'fallo simulado')
    assert run.estado == 'FAILED'
    assert run.error_mensaje == 'fallo simulado'
    assert db.method_calls[0][0] == 'rollback'
    db.commit.assert_called_once()


def test_error_rows_do_not_mutate_input():
    db = MagicMock()
    row = {'id': 1, '_errores_detectados': ['dato inválido']}
    LoaderStage(db).save_errors([row], __import__('uuid').uuid4(), 'ventas')
    assert row['_errores_detectados'] == ['dato inválido']


def test_api_does_not_report_failed_run_as_success():
    with patch('app.api.routes.pipeline.PipelineOrchestrator') as factory:
        result = factory.return_value.run.return_value
        result.estado = 'FAILED'
        result.to_dict.return_value = {'estado': 'FAILED'}
        with pytest.raises(HTTPException) as error:
            run_pipeline('ventas', MagicMock())
        assert error.value.status_code == 500


def test_invalid_source_never_starts_pipeline():
    with patch('app.api.routes.pipeline.PipelineOrchestrator') as factory:
        with pytest.raises(HTTPException) as error:
            run_pipeline('fuente_inexistente', MagicMock())
        assert error.value.status_code == 400
        factory.assert_not_called()


def test_batch_with_failed_source_is_not_success():
    from types import SimpleNamespace
    from app.api.routes.pipeline import run_all_pipelines
    def result(state):
        return SimpleNamespace(estado=state, total_registros=1, registros_validos=1,
                               registros_error=0, to_dict=lambda: {'estado': state})
    with patch('app.api.routes.pipeline.PipelineOrchestrator') as factory:
        factory.return_value.run.side_effect = [result('FAILED')] + [result('COMPLETED')]*5
        with pytest.raises(HTTPException) as error:
            run_all_pipelines(MagicMock())
        assert error.value.status_code == 500
        assert error.value.detail['estado'] == 'FAILED'
