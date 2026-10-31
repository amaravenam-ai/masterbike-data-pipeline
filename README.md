# MasterBike Data Pipeline

Proyecto de portafolio de Ariel Aravena: pipeline ETL con seis fuentes JSON sintéticas, FastAPI, PostgreSQL y dashboard. Es independiente de MasterBike microservicios: no consume automáticamente sus API ni usa sus bases. Código propio declarado por su titular; preparación y revisión con asistencia de Codex.

## Ejecutar la demostración local

Requisitos: Docker Compose con conectividad para obtener las imágenes. Copiar `.env.example` a `.env` y asignar una contraseña local nueva a POSTGRES_PASSWORD (caracteres alfanuméricos para evitar ambigüedad de URL). No subir `.env`.

```sh
docker compose up --build -d
```

Dashboard: http://127.0.0.1:8097. API: http://127.0.0.1:8097/api/docs.

```sh
curl -X POST http://127.0.0.1:8097/api/v1/pipeline/run/ventas
curl http://127.0.0.1:8097/api/v1/pipeline/runs
docker compose stop
```

El proyecto Compose y sus volúmenes son independientes. No cambies su nombre para reutilizar bases existentes. `docker compose down` conserva los datos de sus volúmenes; no usar `down -v` si necesitas conservarlos.

## Pruebas

Python 3.12 en entorno virtual:

```sh
python -m pip install -r requirements.txt
python -m pytest tests -q
```

Verificación local del 31-10-2026: **74 pruebas aprobadas, sin omisiones**: 63 sin base y 11 con PostgreSQL 16 real en esquemas temporales aislados. Se comprobaron las seis fuentes, repetición, entrada vacía, archivos ausentes/ilegibles y correspondencia del gráfico con las filas almacenadas. La ejecución final registró 1295 advertencias de deprecación (incluyen datetime.utcnow y parámetros example de FastAPI); no se presentan como errores ni se ocultan.

Para probar PostgreSQL real, iniciar solo la base y definir PORTFOLIO_TEST_DATABASE_URL con la contraseña local:

```sh
docker compose up -d postgres
# PORTFOLIO_TEST_DATABASE_URL=postgresql://portfolio:CLAVE_LOCAL@127.0.0.1:55437/portfolio_pipeline
python -m pytest tests/integration -q
```

La suite permite solo una base local con prefijo portfolio_; crea y elimina un esquema aleatorio propio, sin borrar tablas existentes.

## Comportamiento y límites

- Ingesta → validación → transformación → carga de raw/clean/error por fuente.
- Usuarios/contactos y direcciones de los ejemplos fueron reemplazados por datos ficticios. Los errores deliberados se conservan para demostrar rechazo.
- Cada carga crea un run_id nuevo. Repetir una fuente añade otra ejecución: no es una actualización idempotente.
- Hay commits por etapa. Un fallo puede dejar raw o clean ya persistidos; no se promete atomicidad del pipeline completo.
- Se hace rollback antes de registrar un fallo; una ejecución FAILED de una fuente o del lote responde HTTP 500. Si falla la conexión inicial puede no crearse un run.
- No hay autenticación para uso público en Internet. El despliegue propuesto escucha solo en localhost y el dashboard consume la API desde el mismo origen; no se habilita CORS global. El scanner de seguridad incorporado es orientativo y no certifica seguridad.
- Dashboard verificado en Chrome: Ejecutar Todos procesó las seis fuentes. Se comprobaron API, conteos y persistencia tras reiniciar PostgreSQL y recrear la API. Con la base detenida, una carga devolvió HTTP 500.
- Los eventos de logs y algunas métricas de monitoreo se mantienen en memoria y se reinician con el proceso; el historial y los registros ETL se almacenan en PostgreSQL.
- El pipeline no entrena modelos: se retiró un nodo visual de entrenamiento sin implementación.
- El arranque reintenta una conexión operativa fallida hasta 15 veces con pausas de dos segundos; al agotar intentos, falla y no anuncia disponibilidad. Los errores de programación no se reintentan.
- La aplicación crea las tablas desde los modelos SQLAlchemy al arrancar; los SQL de sql/ se conservan como referencia académica y no se ejecutan automáticamente ni constituyen un sistema de migraciones versionadas.

Ver `evidencia/resumen.json`, `TERCEROS.md` y `AVISO_DERECHOS.md`.

## Recorrido comprobable

```sh
python scripts/comprobar_demo.py --snapshot .local/demo-runs.json
docker compose stop
docker compose up -d
python scripts/comprobar_demo.py --snapshot .local/demo-runs.json --verificar-persistencia
```

El script espera hasta 60 segundos a que la API esté disponible. La primera llamada crea siete ejecuciones (las seis fuentes y una repetición de ventas); la segunda solo consulta sus IDs. Los snapshots son locales, no se publican.

| Fuente | Procesados | Válidos | Rechazados |
|---|---:|---:|---:|
| ventas | 45 | 35 | 10 |
| usuarios | 43 | 35 | 8 |
| inventario | 43 | 35 | 8 |
| arriendos | 40 | 31 | 9 |
| bicicletas | 42 | 33 | 9 |
| despachos | 42 | 33 | 9 |

Ver [reglas por fuente](docs/REGLAS_DATOS.md) y [captura de la demostración](evidencia/dashboard.png). Los conteos del lateral acumulan ejecuciones; el gráfico corresponde a la última de la fuente seleccionada. La automatización ejecuta la suite con PostgreSQL aislado. Consultar [GitHub Actions](https://github.com/amaravenam-ai/masterbike-data-pipeline/actions) para el estado de cada commit publicado.

![Dashboard con datos sintéticos](evidencia/dashboard.png)
