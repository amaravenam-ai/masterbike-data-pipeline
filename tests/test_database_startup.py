from unittest.mock import patch
import pytest
from sqlalchemy.exc import OperationalError
from app.database.connection import Base, init_db


def test_startup_recovers_when_postgres_is_still_starting():
    failure = OperationalError('connect', {}, Exception('database is starting up'))
    with patch.object(Base.metadata, 'create_all', side_effect=[failure, None]) as create:
        with patch('app.database.connection.time.sleep') as sleep:
            init_db(attempts=3, delay=2)
    assert create.call_count == 2
    sleep.assert_called_once_with(2)


def test_startup_fails_after_bounded_attempts():
    failure = OperationalError('connect', {}, Exception('database unavailable'))
    with patch.object(Base.metadata, 'create_all', side_effect=failure) as create:
        with patch('app.database.connection.time.sleep'):
            with pytest.raises(OperationalError):
                init_db(attempts=3, delay=0)
    assert create.call_count == 3


def test_programming_error_is_not_retried():
    with patch.object(Base.metadata, 'create_all', side_effect=ValueError('invalid schema')) as create:
        with pytest.raises(ValueError):
            init_db(attempts=3, delay=0)
    create.assert_called_once()
