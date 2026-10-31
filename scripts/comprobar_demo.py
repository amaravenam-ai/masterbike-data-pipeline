"""Comprueba la API local; crea ejecuciones sintéticas y verifica su persistencia."""
import argparse
import json
import time
from pathlib import Path
import urllib.error
import urllib.request

BASE = 'http://127.0.0.1:8097'
SOURCES = ['ventas', 'usuarios', 'inventario', 'arriendos', 'bicicletas', 'despachos']


def request(path, method='GET'):
    req = urllib.request.Request(BASE + path, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def check_runs(runs):
    for run in runs:
        code, stored = request('/api/v1/pipeline/runs/' + run['run_id'])
        assert code == 200 and stored['estado'] == 'COMPLETED', stored
        for key in ['total_registros', 'registros_validos', 'registros_error']:
            assert stored[key] == run[key], (key, stored, run)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--verificar-persistencia', action='store_true')
    parser.add_argument('--espera', type=int, default=60)
    args = parser.parse_args()
    deadline = time.monotonic() + args.espera
    while True:
        try:
            code, _ = request('/api')
            if code == 200:
                break
        except (urllib.error.URLError, TimeoutError):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError('La API no está disponible dentro del plazo')
        time.sleep(2)
    if args.verificar_persistencia:
        runs = json.loads(args.snapshot.read_text(encoding='utf-8'))
        check_runs(runs)
        print('Persistencia: todas las ejecuciones y sus conteos se conservan.')
        return
    code, _ = request('/api/v1/pipeline/run/inexistente', 'POST')
    assert code == 400, code
    runs = []
    for source in SOURCES + ['ventas']:
        code, run = request('/api/v1/pipeline/run/' + source, 'POST')
        assert code == 200 and run['estado'] == 'COMPLETED', run
        assert run['total_registros'] == run['registros_validos'] + run['registros_error']
        code, graph = request('/api/pipeline/status?source=' + source)
        assert code == 200 and graph['run_id'] == run['run_id'], graph
        assert graph['registros_procesados'] == run['total_registros']
        assert graph['registros_validos'] == run['registros_validos']
        assert graph['registros_error'] == run['registros_error']
        runs.append(run)
        print(source, run['total_registros'], run['registros_validos'], run['registros_error'])
    assert runs[0]['run_id'] != runs[-1]['run_id']
    check_runs(runs)
    args.snapshot.parent.mkdir(parents=True, exist_ok=True)
    args.snapshot.write_text(json.dumps(runs, indent=2) + '\n', encoding='utf-8')
    print('API, gráfico, repetición e historial: OK')


if __name__ == '__main__':
    main()
